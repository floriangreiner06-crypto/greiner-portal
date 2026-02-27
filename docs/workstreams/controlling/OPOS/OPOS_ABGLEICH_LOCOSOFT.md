# OPOS – Abgleich DRIVE mit Locosoft L362PR (Excel/CSV)

**Stand:** 2026-02-19

## Validierung (warum alte Posten verschwanden)

**Problem:** Es erschienen z. B. 20.000+ Posten inkl. Rechnungen von vor Jahren (2020, 2023). Diese sind in der Praxis längst bezahlt oder ausgebucht.

**Ursache:** In der FIBU werden Zahlungen (Haben) oft **ohne** Zuordnung zur ursprünglichen Rechnungsnummer gebucht (z. B. Sammelzahlung, andere Belegnummer). Die Saldenberechnung **pro Rechnung** (GROUP BY invoice_number, invoice_date) zeigte dann weiterhin „offen“, obwohl der **Kundensaldo** (Summe aller Soll − Haben) bereits ≤ 0 war.

**Lösung in DRIVE:**
1. **Nur Kunden mit positivem Gesamtsaldo:** Es werden nur noch Posten von Debitoren angezeigt, deren **Gesamtsaldo** (alle Buchungen 150000–199999) **> 0** ist. Damit verschwinden „Schein-offene“ Einzelrechnungen von bereits ausgeglichenen Kunden.
2. **Nur offene Buchungszeilen (Auszifferungsnummer):** In Locosoft sind bezahlte Rechnungen mit einer **Auszifferungsnummer** (`clearing_number`) gekennzeichnet, offene mit **„OP“**. DRIVE berücksichtigt in der Saldenberechnung und in der OPOS-Liste nur noch Buchungszeilen, bei denen **`clearing_number IS NULL OR clearing_number = 0`** ist. Ausgezifferte (bezahlte) Zeilen werden nicht mehr mitgezählt – die Liste zeigt nur noch echte offene Posten wie in Locosoft L352PR/L362PR.
3. **Standardfilter „Von“:** Beim ersten Laden wird „Von“ auf „vor 24 Monaten“ gesetzt, damit standardmäßig nur noch Rechnungen der letzten 24 Monate sichtbar sind. Filter kann gelöscht werden für komplette Auswertung.

## Unterschiede

| Aspekt | Locosoft L362PR (Excel/CSV) | DRIVE OPOS |
|--------|-----------------------------|------------|
| **Stichtag** | Report „per [Datum]“ – nur Posten, die **zum Stichtag** noch offen waren | Aktueller Stand der gespiegelten Tabelle `loco_journal_accountings` (kein Stichtag in der Saldenlogik) |
| **Zeilen** | Pro **Buchungsposten** (eine Zeile pro Soll/Haben-Buchung) | Pro **offene Rechnung** (aggregiert: Kunde + Rechnungsnr. + Rechnungsdatum, Saldo = Summe Soll − Haben) |
| **Kundenname** | Spalte „Name“ aus Locosoft-Kundenstamm | Aus `loco_customers_suppliers`; wenn kein Treffer: Anzeige „Kunde Nr. …“ |
| **Debitoren** | Dialog 10000–9999999 (alle Personenkonten) | DRIVE: nur **Forderungen** (140001, 150000–159999, 170000–199999); **Kreditoren 160000–169999** (Einkaufsrechnungen) ausgeschlossen |

## So vergleichen

1. **Stichtag:** Im Locosoft-Export steht z. B. „per 19.02.26“. In DRIVE Filter **Bis** auf denselben Tag setzen (filtert nach Rechnungsdatum; entspricht nicht exakt dem Stichtag-Saldo in Locosoft, da wir keine buchungsdatum-basierte Saldenberechnung haben).
2. **Summen:** Gesamtsumme offen in DRIVE mit „Kd. Saldo kum.“ bzw. Summe der Postensaldi im Locosoft-Export vergleichen.
3. **Kunde leer / „Kunde Nr. X“:** Wenn die Kundennummer aus der FIBU in `loco_customers_suppliers` nicht vorkommt (Sync-Lücke oder anderer Stamm), zeigt DRIVE „Kunde Nr. &lt;Nummer&gt;“. Dann prüfen, ob der Kunde in Locosoft existiert und ggf. der Sync der Kundenstammdaten.

## Datenstand / „Diese Posten sind doch schon bezahlt“

Die OPOS-Liste in DRIVE basiert auf dem **aktuellen Stand der gespiegelten FIBU-Daten** (`loco_journal_accountings`). Wenn in Locosoft gerade Zahlungen oder Ausbuchungen gebucht wurden, können diese bis zum nächsten Sync in DRIVE noch fehlen – die Anzeige wirkt dann „zu viele“ oder „veraltet“. Für eine **verbindliche Prüfung** sollte die Buchhaltung weiterhin Locosoft L362PR „Unausgeglichene Personenkonten“ mit Stichtag nutzen. Auf der OPOS-Seite ist ein Hinweis zu diesem Datenstand eingeblendet.

**Typische Fälle, in denen ein Posten in DRIVE noch „offen“ erscheint, obwohl er wirtschaftlich ausgeglichen ist:**
- **Auszahlung der Leasinggesellschaft:** Die Zahlung läuft über die Leasinggesellschaft (anderer Zahlungsstrom/Beleg); in der FIBU wird sie oft nicht der Einzelrechnung zugeordnet. Die Rechnung bleibt in unserer Sicht solange „offen“, bis sie in Locosoft explizit ausgeglichen oder abgeschrieben wird (oder der Kundensaldo durch andere Buchungen auf ≤ 0 geht).
- Sammelzahlungen ohne Rechnungszuordnung, Ausbuchungen auf anderen Belegen – siehe auch Abschnitt „Validierung“ oben.

### Warum wir den Ausgleich nicht erkennen (z. B. Hofmark Apotheke, Saldo 0 in Locosoft)

Wenn in Locosoft beim Kunden **Gesamtsaldo / Kontensaldo = 0** angezeigt wird, DRIVE aber weiterhin einen offenen Posten für diesen Kunden zeigt, liegt das fast immer an einer von zwei Ursachen:

1. **Zahlung unter anderem Personenkonto gebucht**  
   DRIVE bildet den Kundensaldo aus `loco_journal_accountings` und gruppiert nach **`customer_number`** (L.-Nr / Personenkonto). Wird die Auszahlung der Leasinggesellschaft (oder eine andere Zahlung) als **Haben auf einem anderen Personenkonto** gebucht (z. B. Leasinggeber, Clearingkonto oder ohne Kundennummer), erscheint diese Buchung in unserer Saldenberechnung **nicht** beim Kunden (z. B. 7702408). Beim Kunden bleibt nur die Rechnung (Soll) → Saldo > 0 → Posten erscheint in OPOS. Locosoft kann den Saldo dagegen z. B. über das FiBu-Konto oder eine andere Aggregation ausweisen, sodass dort 0 rauskommt.

2. **Sync-Verzögerung**  
   Die Zahlung ist in Locosoft schon gebucht, im Spiegel `loco_journal_accountings` aber noch nicht angekommen.

**Diagnose im Spiegel (Beispiel Hofmark Apotheke, L.-Nr 7702408):**  
In der Portal-DB prüfen, ob für diese Kundennummer überhaupt Haben-Buchungen im Debitorenbereich vorkommen und ob die Summe Soll − Haben für `customer_number = 7702408` wirklich > 0 ist:

```sql
-- Saldo und Buchungsanzahl pro customer_number (nur Debitorenbereich wie OPOS)
SELECT
  customer_number,
  SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 AS saldo_eur,
  COUNT(*) FILTER (WHERE debit_or_credit = 'S') AS anzahl_soll,
  COUNT(*) FILTER (WHERE debit_or_credit = 'H') AS anzahl_haben
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 140000 AND 199999
  AND (nominal_account_number < 160000 OR nominal_account_number >= 170000)
  AND customer_number = 7702408
GROUP BY customer_number;
```

- Ist **saldo_eur > 0** und **anzahl_haben = 0** → Die Zahlung liegt im Spiegel entweder unter einer anderen `customer_number` oder ist noch nicht synchronisiert. Dann kann DRIVE den Ausgleich nicht erkennen.
- Ist **saldo_eur = 0** im Spiegel, der Kunde erscheint in OPOS aber trotzdem → Filter/Datum prüfen oder Cache; dann wäre es ein Bug.

Hinweis aus Locosoft L111PR: Wenn beim Kunden **„FiBu-Konto-Nummer BS xx“** leer ist, können Buchungen in Locosoft ggf. anders zugeordnet sein; unser Spiegel nutzt jedoch die **`customer_number`** aus der Buchungszeile, nicht das FiBu-Konto aus dem Kundenstamm.

## Technik

- **DRIVE:** `api/opos_api.py`, Abfrage auf `loco_journal_accountings`, `sales`, `employees`, `loco_customers_suppliers` (Portal-PostgreSQL, Spiegel von Locosoft).
- **Auszifferung (Locosoft-Konvention):** Spalte `clearing_number` in `journal_accountings`/`loco_journal_accountings`: **NULL oder 0** = offener Posten („OP“), **numerischer Wert** = ausgeziffert (bezahlt). Die OPOS-Liste filtert auf `clearing_number IS NULL OR clearing_number = 0`, damit nur unausgeglichene Posten erscheinen.
- **Stellantis Bank (Kunde 1007422):** In der FIBU erscheinen Bank-Forderungen unter 1007422; in `sales` ist oft der **Endkunde** (z. B. Petra Cornely) als Käufer eingetragen, nicht die Bank. Daher wird bei 1007422 bei mehreren Verkäufen am gleichen Datum der Verkäufer über **Betragsnähe** ermittelt: Der Sale mit dem kleinsten `ABS(out_sale_price - saldo_eur)` wird zugeordnet (z. B. Stellantis Bank 19.500 € → Verkauf 20.795 € → Rafael).
- **Aktualität:** Abhängig vom Sync-Zeitpunkt von `loco_journal_accountings` und `loco_customers_suppliers`.

Eine echte **Stichtag-Saldenlogik** (nur Buchungen mit Buchungsdatum ≤ Stichtag für die Saldenberechnung) wäre eine Erweiterung und würde die Abfrage deutlich verändern.
