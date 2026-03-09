# Tagesumsätze und -erträge (Locosoft 272/273) – Datenverfügbarkeit

**Stand:** 2026-02-26  
**Workstream:** Controlling  
**Frage:** Sind die für die Locosoft-Programme **L272PR** (Fakturaanalyse Dienstleistungen + ET) und **L273PR** (Fakturaanalyse Fahrzeugrechnungen) benötigten Daten in der **Locosoft PostgreSQL** live verfügbar oder über **SOAP SST** beziehbar?

---

## Kurzfassung

| Programm | Zweck | In Locosoft PostgreSQL abfragbar? | SOAP SST? |
|----------|--------|-----------------------------------|-----------|
| **L272PR** | Tagesumsätze/-erträge Dienstleistung + Ersatzteile (Lohn, Teile, Bruttoertrag) | **Ja** – Rohdaten in `invoices`, `labours`, `parts` | **Nein** – keine SOAP-API für 272/273 gefunden |
| **L273PR** | Tagesumsätze/-erträge Fahrzeugrechnungen (NW/GW, Deckungsbeitrag) | **Ja** – in `dealer_vehicles`, `invoices` | **Nein** |

**Wichtig – Aktualität (Buchungen vom 26.02. sichtbar?):** Siehe Abschnitt **„Aktualität der Locosoft-PostgreSQL“** unten. Die Tabellen werden **nicht zwingend in Echtzeit** befüllt; für FIBU (`journal_accountings`) ist dokumentiert: Befüllung **täglich ca. 18:00–19:00 Uhr**. Ob `invoices`/`dealer_vehicles`/`labours`/`parts` tagesaktuell oder im gleichen Lauf kommen, ist im Projekt **nicht dokumentiert** – Klärung bei Locosoft empfohlen.

---

## L272PR: Fakturaanalyse Ausgangsrechnungen Dienstleistungen und ET

### Was L272PR zeigt (aus Screenshots)

- Abgrenzung **nach Rechnungsdatum** (von/bis), optional nach Rechnungsnummern.
- Rechnungsarten: Werkstatt (2), Reklamation (3), intern (4), Barverkauf (5), Garantie (6).
- **Ergebnis:** Lohnleistung gesamt, Lohn-Erlös netto, Lohn Bruttoertrag; ET gesamt, Teile-Erlös netto, Teile Bruttoertrag; Gesamtertrag; Gesamt Erlös, Summe Rg-Endbeträge (inkl. MwSt).
- Stamm-Einstellungen: Arbeitsarten (B-Art), Berechnungsarten (F6), Teilearten (T-Art).

### Daten in Locosoft PostgreSQL (loco_auswertung_db)

| Quelle | Relevante Felder | Nutzung für Tagesumsatz/Ertrag |
|--------|-------------------|---------------------------------|
| **invoices** | `invoice_type`, `invoice_date`, `invoice_number`, `job_amount_net`/`_gross`, `part_amount_net`/`_gross`, `total_net`, `total_gross`, `subsidiary` | Tagesumsatz = Summen nach `invoice_date` und `invoice_type IN (2,3,4,5,6)`. Erlös Lohn/Teile auf Rechnungsebene vorhanden. |
| **labours** | `invoice_type`, `invoice_number`, `order_number`, `net_price_in_order`, `charge_type`, `labour_type`, `usage_value`, `goodwill_percent` | Detail für Lohn-Erlös, Berechnungsarten, AW; Einsatz über `usage_value`/charge_type. |
| **parts** | `invoice_type`, `invoice_number`, `order_number`, `sum`, `parts_type`, `usage_value` | Detail für Teile-Erlös, Teilearten, Einsatz. |
| **charge_types** | `type`, `subsidiary`, `department` | Zuordnung Berechnungsart. |
| **part_types** (bzw. Teilearten-Stamm) | `type`, `description` | Zuordnung Teileart. |

**Bruttoertrag L272PR (Definition):**
- **Lohn Bruttoertrag** = Lohn-Erlös netto − Selbstkostenanteil (Einsatz Lohn aus `labours.usage_value`, ohne charge_type 90–99) − **VAK Fremdleistung** (Einsatzwert aus `labours.usage_value` für charge_type 90–99).
- **Teile Bruttoertrag** = Teile-Erlös netto − Einsatzwert netto (aus `parts.usage_value`).

Das Portal bildet das ab: Lohn-Einsatz nur für charge_type &lt; 90 oder &gt; 99; VAK Fremdleistung = Summe `labours.usage_value` für charge_type 90–99 (Bereich „Fremdleistung“ in L272PR). Lohn Bruttoertrag = Lohn-Erlös netto − Lohn-Einsatz − VAK Fremdleistung.

**Fahrzeug-DB (L273):** Portal nutzt DB = VK − MwSt − Einsatz − variable Kosten **+ Verkaufsunterstützung (VKU)**. Wenn in L273PR „VKH im Deckungsbeitrag berücksichtigt: Nein“ gewählt ist, weicht der Portal-DB um die VKU-Summe nach oben ab; ohne VKU würde der DB teils negativ werden, daher bleibt VKU einbezogen.

**Fazit L272:** Die **Rohdaten** für Tagesumsätze und -erträge (nach Rechnungsdatum) liegen in der Locosoft-PostgreSQL-DB in diesen Tabellen. Eine 1:1-Nachbildung der L272PR-Logik (AW-Rückrechnung, Kulanz-Umschlüsselung, Stornierungen, „nur belegte“ B-Art/T-Art) erfordert fachliche Regeln und ggf. Joins mit Stammdaten; die Basisdaten (Rechnungen, Lohn/Teile-Summen, Datum, Typ) sind abfragbar. **Ob diese Tabellen tagesaktuell (Echtzeit) oder erst abends befüllt werden, siehe Abschnitt „Aktualität“ unten.**

---

## L273PR: Fakturaanalyse erstellte Fahrzeugrechnungen

### Was L273PR zeigt

- Abgrenzung nach Rechnungsdatum; Rechnungsnummern 7 (Neufahrzeug), 8 (Vorführ/Gebraucht/Tageszul.).
- Fahrzeugarten, Verkaufsarten, Fabrikate, Deckungsbeitrag (mit/ohne Verkaufshilfen und Boni).

### Daten in Locosoft PostgreSQL

| Quelle | Relevante Felder | Nutzung |
|--------|-------------------|---------|
| **dealer_vehicles** | `out_invoice_date`, `out_invoice_number`, `out_invoice_type` (7/8), `out_sale_price`, `out_sale_type`, `pre_owned_car_code`, `calc_sales_aid`, `calc_commission_*`, `out_subsidiary`, `out_make_number` | Tagesumsatz Fahrzeug = Summe `out_sale_price` nach `out_invoice_date`; Deckungsbeitrag-Komponenten in `calc_*`. |
| **invoices** | `invoice_type` (7, 8), `invoice_date`, `invoice_number`, `total_gross`, `total_net` | Alternative/Ergänzung für Umsatz nach Rechnungsdatum. |

**Fazit L273:** Tagesumsätze und Deckungsbeitrag-Komponenten für Fahrzeugrechnungen sind aus `dealer_vehicles` und `invoices` abfragbar. DRIVE nutzt diese Tabellen bereits (z. B. Verkauf, Provision, TEK-Fakturierungs-Check in `check_tek_heute_fakturierung.py` mit `invoices` invoice_type 7,8). **Aktualität:** siehe Abschnitt unten.

---

## SOAP / „SST“

- In der Codebase gibt es **keine** SOAP-Methoden oder Doku für **Fakturaanalyse**, **Programm 272/273** oder **Tagesumsätze/Erträge**.
- SOAP wird genutzt für: Stempelzeiten (Werkstatt), Garantie-Schreibzugriffe, Fahrzeuganlage (writeCustomerDetails, writeVehicleDetails), MOBIS, Adressbuch-Lookup.
- **SST** wird im Projekt als „Single Source of Truth“ (z. B. TEK in `controlling_data.py`) verwendet, nicht als Name einer Locosoft-SOAP-API.

**Fazit:** Die benötigten Infos für Tagesumsätze und -erträge müssen aus der **Locosoft PostgreSQL** (live oder über bestehenden Spiegel wie `loco_journal_accountings`/`loco_invoices`) bezogen werden; SOAP SST liefert diese Auswertungen **nicht**.

---

## TEK vs. 272/273

- **TEK** im Portal nutzt **Buchungsdatum** (`journal_accountings.accounting_date`) und FIBU-Konten (810000–889999, 8932xx). Datenquelle: `loco_journal_accountings` (Spiegel in drive_portal).
- **272/273** nutzen **Rechnungsdatum** und Rechnungsebene (Lohn/Teile/Fahrzeug). Datenquelle: Locosoft-Tabellen **invoices**, **labours**, **parts**, **dealer_vehicles** (auf 10.80.80.8 oder gespiegelt z. B. als `loco_invoices` im Portal). Ob diese Tabellen tagesaktuell befüllt werden, siehe Abschnitt „Aktualität“.

Für eine **tagesaktuelle Anzeige „Tagesumsatz/-ertrag“ wie in 272/273** im Portal wäre eine eigene Abfrage auf **invoices** (und für Detail Lohn/Teile: labours, parts) nach **invoice_date** bzw. auf **dealer_vehicles** nach **out_invoice_date** nötig – ohne SOAP.

---

## Aktualität der Locosoft-PostgreSQL („Sehen wir jetzt Buchungen vom 26.02.?“)

Die Locosoft-PostgreSQL (loco_auswertung_db auf 10.80.80.8) wird **nicht zwingend in Echtzeit** befüllt. Im Projekt ist dokumentiert:

| Daten / Tabelle | Dokumentierte Aktualität | Buchungen vom heutigen Tag (z. B. 26.02.) vor 18–19 Uhr sichtbar? |
|-----------------|---------------------------|-------------------------------------------------------------------|
| **journal_accountings** (FIBU, TEK, BWA, Kontenübersicht) | Locosoft befüllt die DB **täglich ca. 18:00–19:00 Uhr**. TEK „Aktueller Monat“ = typ. 1. bis **gestriges** Datum. | **Nein** – vor dem Abend-Lauf sehen wir in der Regel **keine** Buchungen vom 26.02. |
| **invoices**, **dealer_vehicles**, **labours**, **parts** | **Nicht dokumentiert.** Unklar, ob Locosoft diese Tabellen in Echtzeit schreibt oder im gleichen Abend-Batch wie journal_accountings. | **Unklar** – ohne Klärung bei Locosoft kann nicht davon ausgegangen werden, dass wir **jetzt gerade** Rechnungen/Buchungen vom 26.02. sehen. |

**Fazit:**

- **FIBU (journal_accountings):** Stand heute **nicht** tagesaktuell – Buchungen vom 26.02. erscheinen typisch **erst nach dem Abend-Update** (ca. 18–19 Uhr).
- **272/273-relevante Tabellen (invoices, dealer_vehicles, labours, parts):** Die **Struktur** ist in PostgreSQL vorhanden und abfragbar. Ob der **Inhalt** tagesaktuell ist (d. h. wir sehen „jetzt“ Rechnungen vom 26.02.), ist **im Projekt nicht festgehalten**. Dafür müsste entweder ein Test (Abfrage auf Rechnungen mit heute-Datum zu unterschiedlichen Tageszeiten) oder eine **Rückfrage bei Locosoft** klären, ob diese Tabellen live/fortlaufend oder nur im gleichen Abend-Lauf aktualisiert werden.

**Empfehlung:** Bei Locosoft nachfragen: Werden `invoices`, `dealer_vehicles`, `labours`, `parts` in der Auswertungs-PostgreSQL **in Echtzeit** (bzw. bei jeder Fakturierung/Buchung) aktualisiert oder nur im **täglichen Lauf (z. B. 18–19 Uhr)** wie journal_accountings?

---

## Praxistest 26.02.2026: Rechnung 1129851 (heute fakturiert)

Eine am **26.02.2026** fakturierte Werkstatt-Rechnung (L272PR Einzelanzeige: Nr. **1129851**, Datum 26.02.26, Auftrag 41321, Dullinger Power, ET-Positionen „GRIFF HECKKLAPPE“ 49,73 € + „FRACHT FRACHTKOSTEN“ 8,90 €, Forderung 69,77 €) wurde in der **Locosoft PostgreSQL** abgefragt:

| Tabelle   | Befund |
|-----------|--------|
| **invoices** | **Vorhanden:** invoice_type=2, invoice_number=1129851, invoice_date=2026-02-26, total_gross=69,77, part_amount_net=58,63, order_number=41321, paying_customer=1005088. |
| **parts**    | **Vorhanden:** 2 Positionen zu Rechnung 1129851 (Auftrag 41321): Teile-Nr. 39007842 „GRIFF, HECKKLAPPE“ 49,73 €; FRACHT/FRACHTKOSTEN 8,90 €. |

Zusätzlich: Am selben Tag wurden **32 Rechnungen** mit `invoice_date = 2026-02-26` in `invoices` gefunden (inkl. 1129851). **Fazit:** Die Tabellen **invoices** und **parts** sind für diese heute fakturierte Rechnung **tagesaktuell** in der Auswertungs-PostgreSQL sichtbar – sie werden also **nicht** erst im Abend-Lauf (18–19 Uhr) befüllt, sondern mit kurzer Latenz bzw. in Echtzeit nach Fakturierung. Für **journal_accountings** (FIBU) gilt weiterhin die dokumentierte Abend-Befüllung.

---

## Abweichung Fahrzeug-DB (L273PR vs. Portal)

**Woher kommt die Abweichung (z. B. 206,77 €)?**  
Die Differenz kommt **nahezu vollständig von der Verkaufsunterstützung (VKU)**. Das Portal rechnet den Fahrzeug-DB mit **+ VKU** (Formel: `DB = VK − MwSt − Einsatz − variable Kosten + VKU`). In L273PR kann „VKH im Deckungsbeitrag berücksichtigt: **Nein**“ gewählt sein – dann erscheint in L273PR **kein** VKU im DB. In dem Fall gilt: **Portal-DB − L273PR-DB ≈ Summe VKU des Tages**. Die API liefert diese Summe als `fahrzeug_vku_sum` (z. B. 206,77 €), damit die Anzeige die Abweichung erklären kann.

**Weitere mögliche Ursachen (meist klein):**

1. **Anzahl/Filter:** L273PR zeigt „Gültige“ Fahrzeuge; das Portal summiert alle Verkäufe mit `out_invoice_date` am Tag. Abweichungen bei Filterung möglich.
2. **Stichtag:** Beide nutzen Rechnungsdatum; Zeitzone oder Auswertungszeitpunkt können minimal abweichen.
3. **Berechnung:** Portal nutzt `deckungsbeitrag = out_sale_price - mwst - einsatzwert - variable_kosten + vku` (VKU aus `dealer_sales_aid.claimed_amount`). L273PR kann andere Abzüge oder Einsatzwert-Definitionen haben.
4. **Einsatzwert:** Portal-Einsatz aus Locosoft calc_*-Felder; Locosoft kann weitere Posten (Versicherung, externe Einsatzerhöhung) einrechnen.

**Empfehlung:** Die Abweichung entspricht in der Regel der **VKU-Summe des Tages** (`fahrzeug_vku_sum`). Bei weiteren Differenzen Stichprobe (einzelne Rechnungen/VIN) in L273PR und Portal vergleichen.

---

## Nächste Schritte (optional)

1. **Aktualität klären:** Bei Locosoft erfragen, ob `invoices`, `dealer_vehicles`, `labours`, `parts` in der Auswertungs-DB tagesaktuell oder nur im Abend-Lauf befüllt werden (siehe Abschnitt „Aktualität“).
2. **Spiegel prüfen:** Ob `loco_invoices` (und ggf. labours/parts) im Portal aktuell gespiegelt werden und mit welcher Latenz (vgl. Locosoft-Befüllung ca. 18–19 Uhr für journal_accountings).
3. **API/Report:** Endpoint oder Report „Tagesumsatz 272/273“ auf Basis von `invoices` + `dealer_vehicles` (nach Klärung der Aktualität) definieren.
4. **Abgleich:** Einmalig L272PR/L273PR (Locosoft) vs. Portal-Aggregation (gleicher Tag, gleiche Filter) zum Validieren.
