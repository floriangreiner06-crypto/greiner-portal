# OPOS-Modul (Offene Posten) – Konzept

**Stand:** 2026-02-19  
**Workstream:** Controlling

## Ausgangslage

- Die Buchhaltung schickt wöchentlich **offene Posten aus dem Fahrzeugverkauf**, gruppiert nach Verkäufer.
- Erster Ansatz: reine SQL-Abfrage auf `loco_journal_accountings` (Debitoren) + Verkäufer-Zuordnung.
- **Ansprechpartner (Verkäufer / Rechnungsersteller):**
  - **Fahrzeugverkauf:** Verkäufer aus **Ablieferung** (`sales`), Match Rechnungsnr+Datum oder Kunde+Datum. (Bei Fz-Verkauf schreibt der Verkäufer die Rechnung nicht; die Info steht nur in der Verkaufs-Rechnung, nicht in der Locosoft-OPOS-Liste.)
  - **Sonstige Rechnungen:** Rechnungsersteller aus **FIBU** `employee_number` (= „Mitarbeiter“ wie in L362PR). Ausgabe mit Kennzeichnung **ist_fahrzeugverkauf** (true/false).

## Vorschlag: OPOS als Modul in DRIVE

Statt nur eine Einzelabfrage zu haben, ein **OPOS-Modul** mit Filter und Reporting – das ist der bessere Ansatz:

- **Eine fachliche Heimat** für „offene Posten“ (nicht versteckt in Scripts/SQL).
- **Filter:** Zeitraum, Verkäufer, Kunde, Betrag (min/max), „nur mit Verkäufer“ / „nur Fahrzeugverkauf“, Debitorenbereich.
- **Reporting:** Liste wie Buchhaltung (gruppiert nach Verkäufer), Summen pro Verkäufer/Kunde, Export CSV/Excel.
- **Erweiterbar:** später z. B. Mahnstufen, Fristen, Verknüpfung zu Buchhaltungs-Exporten.

### Einordnung

- **Menü:** Controlling → **Offene Posten (OPOS)** (oder Unterpunkt unter Finanzen/Bankenspiegel, je nach Navigation).
- **Berechtigung:** wie andere Controlling-Seiten (z. B. `controlling`-Feature, ggf. Rolle Buchhaltung/Geschäftsleitung).

### Grobe Funktionsumfänge

| Bereich | Inhalt |
|--------|--------|
| **Datenbasis** | Offene Salden aus `loco_journal_accountings` (Debitoren 150000–199999), aggregiert pro Kunde/Rechnung/Datum. |
| **Ansprechpartner** | Fahrzeugverkauf: Verkäufer aus **`sales`** (Ablieferung). Sonstige: Rechnungsersteller aus **FIBU** `employee_number` (L362PR „Mitarbeiter“). Name aus `employees` (locosoft_id). Spalte `ist_fahrzeugverkauf` zur Filterung. |
| **Filter** | Zeitraum (Rechnungsdatum), Verkäufer (Dropdown), Kunde (Suche/Text), Betrag min/max, „nur mit Verkäufer“, „nur Ohne Verkäufer“. |
| **Ansicht** | Tabelle: Verkäufer, Kunde, Rechnungsdatum, Rechnungsnr, Betrag (EUR); Sortierung u. a. nach Verkäufer, Datum. |
| **Reporting** | Gruppierung nach Verkäufer (wie Buchhaltungsliste), Summen pro Verkäufer; Export CSV/Excel. |
| **Technik** | API (z. B. `api/opos_api.py` oder Erweiterung `controlling_api`), Route unter `/controlling/opos`, Template `controlling/opos.html`, Nutzung bestehender SSOT (loco_journal_accountings, sales, employees, loco_customers_suppliers). |

### Nächste Schritte (optional)

1. **Navigation:** Eintrag „Offene Posten“ unter Controlling (DB-Navigation oder Fallback in base).
2. **API:** Endpoint z. B. `GET /api/controlling/opos?von=&bis=&verkaeufer=&nur_mit_verkaeufer=` mit gleicher Logik wie in `scripts/sql/offene_posten_fahrzeugverkauf.sql`.
3. **Seite:** Filterformular + Tabelle + „Nach Verkäufer gruppieren“ + Export-Button.
4. **Verkäufer-Zuordnung:** Bereits in SQL über `sales` abgebildet; bei Bedarf mit Buchhaltung klären, ob FIBU-Rechnungsnummern für Fahrzeugverkauf mit Locosoft übereinstimmen (dann mehr Treffer über Rechnungsnr+Datum).

---

**Fazit:** Ja – Verkäufer-Zuordnung über Ablieferung in DRIVE (sales) ist der richtige Zusammenhang; die SQL-Abfrage ist darauf umgestellt. Ein **OPOS-Modul** mit Filter und Reporting ist sinnvoll und kann schrittweise umgesetzt werden.
