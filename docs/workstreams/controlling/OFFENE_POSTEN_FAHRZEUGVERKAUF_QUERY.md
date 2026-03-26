# Offene Posten aus dem Fahrzeugverkauf – Abfrage

**Zweck:** Abfrage auf die Portal-DB (mit Locosoft-Spiegeln), die eine Auswertung ähnlich der wöchentlichen Liste der Buchhaltung liefert: offene Forderungen aus dem Fahrzeugverkauf, gruppierbar nach Verkäufer.

## Format der Buchhaltungsliste (Beispiel)

- **Rafael Kraus:** Maximilian Haydn, Rest aus Rechnung vom 04.02.26 EUR 15.500,-- (Santander Bank Finanzierung)
- **Daniel Fialkowski / Florian Pellkofer / Anton Süß:** Stellantis Bank / Hans-Peter Greil, Rechnung vom 12.02.26 EUR 31.040,--
- **Edeltraud Punzmann / Roland Schmid / Michael Penn:** mehrere Positionen (Leasys, Niemeier, Ambulanter Pflegedienst …)
- **Marius Löbel / Rolf Sterr:** (keine Einträge im Beispiel)
- **Ohne Verkäufer:** Positionen, die sich keiner Verkäufer-Rechnung zuordnen lassen

## Datenbasis

- **Offene Posten:** Aus Locosoft-FIBU (`loco_journal_accountings`). Nur **Forderungen** (Debitoren): 140001, 150000–159999, 170000–199999. **Kreditoren 160000–169999** (Einkaufsrechnungen) sind ausgeschlossen.
- **Saldo:** Pro Kunde/Rechnung (customer_number, invoice_number, invoice_date) wird der offene Betrag als Summe Soll minus Haben berechnet. `posted_value` in Locosoft ist in **Cent** – für die Anzeige in Euro durch 100 teilen.
- **Ansprechpartner (Verkäufer bzw. Rechnungsersteller):**
  - **Fahrzeugverkauf:** Verkäufer aus **Ablieferung** (`sales`): Match Rechnungsnr+Datum oder Kunde+Datum. (Bei Fz-Verkauf schreibt nicht der Verkäufer die Rechnung; die Locosoft-OPOS-Liste hat diese Info nicht – nur die Verkaufs-Rechnung.)
  - **Sonstige Rechnungen** (Werkstatt, Teile, …): **Rechnungsersteller** aus FIBU `employee_number` (= „Mitarbeiter“ wie in L362PR). Name über **employees** (locosoft_id). Spalte **ist_fahrzeugverkauf** zeigt an, ob die Zuordnung aus `sales` stammt.
- **Kundenname:** Aus **loco_customers_suppliers** (family_name, first_name).

## Einschränkungen

1. **Fahrzeugverkauf:** Verkäufer erscheint nur, wenn die offene Position einer Ablieferung in `sales` zugeordnet werden kann (Rechnungsnr+Datum oder Kunde+Datum). Wenn das Rechnungsformat in der FIBU von Locosoft/Verkauf abweicht, fehlt der Match – dann wird der Rechnungsersteller (FIBU) angezeigt.
2. **Debitorenbereich:** 150000–199999. Falls euer Kontenplan abweicht, im SQL den Filter `nominal_account_number BETWEEN 150000 AND 199999` anpassen.
3. **Aktualität:** Abhängig vom Sync der Locosoft-Spiegel und der Tabelle `sales`.

## SQL (Portal-DB)

Die Abfrage liegt in:

- **`scripts/sql/offene_posten_fahrzeugverkauf.sql`**

Ausführung z. B.:

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f scripts/sql/offene_posten_fahrzeugverkauf.sql
```

Optional: Ausgabe nach Verkäufer sortiert oder in ein CSV/Excel exportieren und dort nach Verkäufer gruppieren (wie in der Buchhaltungsliste).

### Nur Fahrzeugverkauf anzeigen

- Im Ergebnis die Spalte **ist_fahrzeugverkauf** = true filtern; dann nur Posten, bei denen der Ansprechpartner der **Verkäufer** aus der Ablieferung ist.
- Wenn in der Query nur Fahrzeugverkauf ausgegeben werden soll: in der CTE `mit_verkaeufer` z. B. `WHERE verkaeufer_fahrzeugverkauf IS NOT NULL` ergänzen (oder im äußeren SELECT `WHERE ist_fahrzeugverkauf = true`).
