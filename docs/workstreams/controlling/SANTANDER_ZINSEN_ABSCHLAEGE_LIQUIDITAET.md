# Santander & Stellantis: Zinsen und Abschläge in der Liquiditätsvorschau

**Stand:** 2026-03  
**Frage:** Sind die zu erwartenden Zinsen und Abschläge von Santander bzw. Stellantis schon eingebaut? Sind alle Daten vorhanden?

---

## Kurzantwort

| Institut   | Thema (Zinsen)     | Eingebaut? | Daten vorhanden? |
|-----------|--------------------|------------|-------------------|
| **Santander**  | Zinsen             | **Nein**   | **Ja** – `fahrzeugfinanzierungen` (zinsen_letzte_periode aus CSV) |
| **Santander**  | Abschläge/Tilgungen | **Nein**  | **Nein** – CSV nur Bestandsliste, kein Raten-/Tilgungsplan |
| **Stellantis** | Zinsen             | **Nein**   | **Ja** – `fahrzeugfinanzierungen` (zinsen_letzte_periode **berechnet** im Import, 9,03 % p.a.) |
| **Stellantis** | Abschläge/Tilgungen | **Nein**  | **Nein** – Excel/ZIP nur Bestand pro RRDI, keine Ratenliste |

**Hinweis:** Die Liquiditätsvorschau nutzt die Tabelle `tilgungen` nur für **Hyundai** (Scraper + Import). Santander- und Stellantis-Abschläge sind dort nicht vertreten.

---

## 1. Santander: Zinsen

### Daten

- **Quelle:** Santander-Bestandsliste (CSV) → Import `import_santander_bestand.py` → Tabelle **`fahrzeugfinanzierungen`**.
- **Relevante Spalten:** `zinsen_letzte_periode` (aus CSV „Zinsen letzte Periode“), `zins_startdatum`, `zinsen_gesamt`, `finanzinstitut = 'Santander'`.
- **Nutzer:** Einkaufsfinanzierung-Übersicht im Bankenspiegel nutzt diese Daten bereits (z. B. `santander_zinsen_monatlich` als Summe der geschätzten monatlichen Zinsen).

### Liquiditätsvorschau

- Die **Liquiditätsvorschau** (`get_cashflow_vorschau`) berücksichtigt **keine** erwarteten Zinsen aus `fahrzeugfinanzierungen`.
- Sie verwendet nur: Start-Saldo, Transaktionen (IST), **Tilgungen** (aus Tabelle `tilgungen`), erwartete Einnahmen (Ø/Tag).
- **Fazit:** Die Daten für erwartete Santander-Zinsen sind da; eine Einbindung in die Vorschau (z. B. monatliche Zinslast pro Tag oder pro Monat) ist **nicht** umgesetzt. Sie wäre ohne neue Datenquellen möglich (Summe `zinsen_letzte_periode` für Santander, Verteilung auf die Tage/Monate der Projektion).

---

## 2. Stellantis: Zinsen

### Daten

- **Quelle:** Stellantis-Excel aus ZIP (pro RRDI, WHSKRELI_*.zip) → Import `import_stellantis.py` → Tabelle **`fahrzeugfinanzierungen`**.
- **Zinsen:** Im Import **berechnet** (nicht aus Excel gelesen): Festzinssatz **9,03 % p.a.**; `zinsen_letzte_periode` = aktueller_saldo × 9,03 % × 30/365; `zins_startdatum` = heute − (alter_tage − zinsfreiheit_tage). Nur für Fahrzeuge mit alter_tage > zinsfreiheit_tage.
- **Nutzer:** Einkaufsfinanzierung-Übersicht im Bankenspiegel nutzt Stellantis-Zinsen (z. B. `stellantis_zinsen_monatlich`).

### Liquiditätsvorschau

- Wie bei Santander: Die Liquiditätsvorschau berücksichtigt **keine** Zinsen aus `fahrzeugfinanzierungen`. Die Daten sind vorhanden; Einbindung ist **nicht** umgesetzt.

---

## 3. Abschläge (Tilgungen/Raten) – Santander & Stellantis

### Daten Santander

- **Santander-CSV:** Bestandsliste (Finanzierungsnr., VIN, Saldo, Endfälligkeit, Zins Startdatum, Zinsen letzte Periode/Gesamt). **Keine Spalte für Raten oder Tilgungsplan.**

### Daten Stellantis

- **Stellantis Excel (aus ZIP):** Bestandsdaten pro RRDI (Fahrzeuge, Salden, Vertragsbeginn, Zinsfreiheit, alter_tage). **Keine Ratenliste**, kein Tilgungsplan in den beschriebenen Imports.

### Tabelle `tilgungen` und Liquiditätsvorschau

- `tilgungen` wird von der Liquiditätsvorschau genutzt; befüllt wird sie **nur aus dem Hyundai-Tilgungen-Import** (Scraper + `import_hyundai_data.py`). Santander- und Stellantis-Einträge existieren dort **nicht**.
- **Fazit:** Abschläge von Santander und Stellantis sind **nicht** eingebaut und **nicht** abbildbar, solange die Institute keinen Export mit Fälligkeiten und Beträgen (Tilgungsplan/Ratenplan) liefern. Sobald ein solcher Export existiert, kann er – analog zu Hyundai – in `tilgungen` importiert werden und erscheint automatisch in der Vorschau.

---

## 4. Was wäre nötig?

### Zinsen (mit vorhandenen Daten umsetzbar – Santander & Stellantis)

1. In `get_cashflow_vorschau` (oder vorgelagert): Aus `fahrzeugfinanzierungen` für `finanzinstitut IN ('Santander', 'Stellantis')` und `aktiv = true` die Summe `zinsen_letzte_periode` (monatliche Schätzung) ermitteln.
2. Diese Zinslast auf die Tage/Monate der Projektion verteilen (z. B. gleichmäßig pro Monat).
3. In der Projektion als weitere Ausgabe „Erwartete Zinsen (EK-Finanzierung)“ abziehen (analog zu Tilgungen) und optional in der Tabelle „Erwartete Bewegungen“ ausweisen (ggf. getrennt Santander/Stellantis).

### Abschläge (nur mit zusätzlichen Daten)

1. **Klärung:** Gibt es von Santander und/oder Stellantis einen Export „Ratenplan“/„Tilgungsplan“ (CSV/Excel) mit Fälligkeitsdatum und Betrag pro Rate?
2. Wenn **ja:** Parser + Import in `tilgungen` (mit `finanzinstitut = 'Santander'` bzw. `'Stellantis'`) analog zu Hyundai; danach erscheinen die Abschläge automatisch in der Liquiditätsvorschau.
3. Wenn **nein:** Keine echten „erwarteten Abschläge“ möglich; nur Annäherung z. B. über historische Mittelwerte aus kategorisierten Transaktionen (Einkaufsfinanzierung Stellantis/Santander), siehe `PLAN_LIQUIDITAET_KATEGORISIERUNG_TILGUNGEN.md`.

---

## 5. Referenzen

- **Liquiditätsvorschau:** `api/cashflow_vorschau.py` (nutzt `tilgungen`, nicht `fahrzeugfinanzierungen` für Zinsen).
- **Santander-Import:** `scripts/imports/import_santander_bestand.py` (Bestand + Zinsfelder aus CSV).
- **Stellantis-Import:** `scripts/imports/import_stellantis.py` (Excel aus ZIP pro RRDI; Zinsen werden mit 9,03 % p.a. berechnet und in `zinsen_letzte_periode`/`zins_startdatum` geschrieben).
- **Tilgungen-Import:** `scripts/imports/import_hyundai_data.py` (nur Hyundai); `tilgungen`-Struktur mit `finanzinstitut`.
- **Planung/Offen:** `docs/workstreams/controlling/PLAN_LIQUIDITAET_KATEGORISIERUNG_TILGUNGEN.md` (Abschnitt 2: Santander/Stellantis ohne Tilgungsplan).
