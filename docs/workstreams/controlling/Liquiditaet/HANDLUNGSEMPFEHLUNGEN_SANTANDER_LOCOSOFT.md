# Handlungsempfehlungen Zinsen: Santander Einkaufsfinanzierung (Mobilität) & Locosoft

**Stand:** 2026-03  
**Frage:** Sind die Santander-Bedingungen (Einkaufsfinanzierung Mobilität) in den Handlungsempfehlungen berücksichtigt? Können wir die Empfehlung (Stellantis → Santander)? Haben wir die nötigen Flags aus Locosoft?

---

## 1. Ist das bei unseren Handlungsempfehlungen berücksichtigt?

**Ja.** Die Empfehlung **„Umfinanzierung von X Fahrzeugen (über Zinsfreiheit) zu Santander“** ist umgesetzt und wird angezeigt.

- **Logik:** Fahrzeuge, die bei **Stellantis** bereits **über die Zinsfreiheit** sind (`alter_tage > zinsfreiheit_tage`), zahlen dort 9,03 % p.a. Die Empfehlung schlägt vor, diese zu **Santander** umzufinanzieren – dort würden sie (bei Neuaufnahme) in die **günstige Anfangsphase** (laut Kreditrahmenvereinbarung: 1.–90. Tag Zinsaufschlag 2 % auf Euribor) kommen.
- **Santander-Limit:** 1.500.000 € (aus `ek_finanzierung_konditionen` oder Fallback) – entspricht der **Kreditrahmenvereinbarung P@rtnerPlus** (die drei Santander-PDFs im Ordner Liquiditaet).
- **Ersparnis-Annahme:** Stellantis 9,03 % → Santander pauschal **~4,5 %** (Ersparnis 4,53 %). Die echten Santander-Sätze sind **Euribor + Aufschlag** (1.–90. Tag 2 %, danach steigend); 4,5 % ist eine plausible Durchschnittsannahme, könnte später aus der **Modalitäten-DB** (z. B. `zinsaufschlag_1_90_tag` + Euribor) verfeinert werden.

---

## 2. Können wir das?

**Ja.** Die Empfehlung ist fachlich umsetzbar:

- Ablösung bei Stellantis, Neuaufnahme bei Santander im Rahmen der **Einkaufsfinanzierung (Mobilität)** / P@rtnerPlus.
- Ob Santander bei **Umfinanzierung** (kein Neukauf) exakt die gleichen Konditionen wie in der Kreditrahmenvereinbarung gewährt, ist vertraglich zu klären – die technische Logik im Portal ist konsistent (Limit, Salden, Ersparnis-Schätzung).

---

## 3. Hast du die notwendigen Flags aus Locosoft?

**Nein – und es sind keine Locosoft-Flags nötig.** Alle Daten für die Handlungsempfehlungen kommen aus der **Portal-Datenbank** (`fahrzeugfinanzierungen`), befüllt durch die **Bank-/Hersteller-Imports**:

| Was | Quelle | Kein Locosoft |
|-----|--------|----------------|
| **Stellantis:** „über Zinsfreiheit“, „bald ablaufend“ | `zinsfreiheit_tage`, `alter_tage` aus **Stellantis-Excel-Import** (Spalte „Zinsfreiheit (Tage)“) | ✅ |
| **Stellantis:** Zinssatz 9,03 % | `ek_finanzierung_konditionen` oder fest 9,03 | ✅ |
| **Santander:** Saldo, Zinsen | **Santander-CSV-Import** (`zinsen_letzte_periode`, `aktueller_saldo`) | ✅ |
| **Santander:** Limit 1,5 Mio | `ek_finanzierung_konditionen` oder Fallback 1.500.000 | ✅ |
| **Hyundai / Genobank** | jeweilige Imports / Konten | ✅ |

**Locosoft** wird in der Zinsen-Analyse und bei den Umfinanzierungs-Empfehlungen **nicht** verwendet. Optional wird an anderer Stelle **Modell/Kennzeichen** aus Locosoft in die Anzeige angereichert (z. B. Bankenspiegel EK-Übersicht), nicht für die **Zinsfreiheits-** oder **„über Zinsfreiheit“-Logik**.

---

## 4. Santander „Einkaufsfinanzierung (Mobilität)“ aus den PDFs

Die drei Santander-PDFs im Ordner Liquiditaet (Allgemeine Bedingungen, Gebührenverzeichnis, **Kreditrahmenvereinbarung P@rtnerPlus**) beschreiben die **Einkaufsfinanzierung (Mobilität)**. Die **konkreten** Zahlen (Tilgung, Zinsaufschläge, Kreditrahmen) stehen in der **Kreditrahmenvereinbarung** und sind in der **Modalitäten-DB** hinterlegt (`kredit_ausfuehrungsbestimmungen` für Santander), siehe `SANTANDER_PDF_INHALT.md`.

- **Optional:** Die pauschale Santander-Annahme **4,5 %** in der Handlungsempfehlung könnte künftig aus der Modalitäten-DB abgeleitet werden (z. B. Euribor + `zinsaufschlag_1_90_tag` für die ersten 90 Tage nach Umfinanzierung).

---

## 6. Locosoft: Modell + Santander „Mobilität“ für Empfohlene Fahrzeuge

Für die **Handlungsempfehlung Stellantis → Santander** werden die empfohlenen Fahrzeuge mit **Locosoft** angereichert:

- **Modell:** Wenn in `fahrzeugfinanzierungen` kein Modell gefüllt ist, wird aus Locosoft (`vehicles` + `models`/`free_form_model_text`) Modell und ggf. Marke geholt, damit die Fahrzeugliste im Modal durchgängig lesbar ist.
- **Mobilität (Santander):** Anhand der **Locosoft-Felder** wird abgeleitet, ob das Fahrzeug bei Santander unter den **Mobilität-Rahmen** (500k) fallen würde (SSOT der Zins-Optimierung: `api/zins_optimierung_api.py` → `_locosoft_fahrzeuge_fuer_vins()`):
  - **Vorführer/Demo:** `dealer_vehicle_type` IN ('V', 'D')
  - **Tageszulassung:** `dealer_vehicle_type` = 'T'
  - **Neuwagen mit Erstzulassung:** `dealer_vehicle_type` = 'N' **und** `vehicles.first_registration_date` gesetzt (Santander zählt das wie Mobilität/Tageszulassung; siehe **`LOCOSOFT_PROGRAMM_132_ERSTZULASSUNG_MOBILITAET.md`**)
  - **Mietwagen/Vermieter:** `is_rental_or_school_vehicle` = true oder (`dealer_vehicle_type` = 'G' und `pre_owned_car_code` = 'M')
- Die **UI** zeigt in der Empfehlungskarte und im **Modal** („X Fahrzeuge anzeigen“) die Spalte **Mobilität (Santander)** (Ja/Nein) und einen **Hinweis**, wenn für diese Fahrzeuge bei Santander **keine Luft mehr** im Mobilität-Rahmen ist (Belegung + empfohlener Saldo > 500k).

---

**Zusammenfassung:** Die Handlungsempfehlung „Stellantis → Santander (über Zinsfreiheit)“ ist berücksichtigt und umsetzbar; sie nutzt **keine** Locosoft-Flags, sondern ausschließlich Daten aus **fahrzeugfinanzierungen** (Stellantis-Excel, Santander-CSV) und ggf. `ek_finanzierung_konditionen`. Die Santander-Bedingungen (Mobilität) aus den PDFs sind in der Modalitäten-DB abgebildet und können für eine verfeinerte Zinsannahme genutzt werden.

---

## 5. Kreditvolumen Santander: Anteil „Mobilität“ und welche Fahrzeuge zählen

Das Kreditvolumen bei Santander ist geteilt: **Gesamt 1.500.000 €**, davon **max. 500.000 € für Mobilitätsfahrzeuge** (Kreditrahmenvereinbarung P@rtnerPlus).

### Kennen wir den Anteil?

**Ja.** In der **Modalitäten-DB** ist das hinterlegt:

- `kredit_ausfuehrungsbestimmungen` (Santander, vertragsart_id = 3):
  - **regel_key `kreditrahmen_gesamt`** → 1.500.000 €
  - **regel_key `kreditrahmen_mobilitaet`** → 500.000 € (Anteil Mobilität)

Quelle: `migrations/seed_santander_modalitaeten.sql`, siehe auch `SANTANDER_PDF_INHALT.md` (Abschnitt 3.1).

### Wissen wir, welche Fahrzeuge unter „Mobilität“ fallen?

**Ja – für Santander.** Beim **Santander-CSV-Import** wird die **produkt_kategorie** primär aus **Spalte O** (15. Spalte) der CSV gelesen; falls leer, wird sie aus der Spalte **„Produkt“** abgeleitet und in `fahrzeugfinanzierungen.produkt_kategorie` gespeichert:

| produkt_kategorie   | Bedeutung / Vertragsseite        |
|---------------------|-----------------------------------|
| **Mobil/Vermieter** | aus Produktpfad „Mobil/Vermieter“ |
| **Vorführer**       | aus Produktpfad „Mobil/Vorführer“ |
| Neuwagen            | aus Produktpfad „…/Neu“           |
| Gebraucht           | aus Produktpfad „…/Gebraucht“    |

**Mobilitätsfahrzeuge** im Sinne der Kreditrahmenvereinbarung (max. 500k) sind damit die Einträge mit **produkt_kategorie IN ('Mobil/Vermieter', 'Vorführer')**. Alle anderen Santander-Positionen (Neuwagen, Gebraucht) zählen zum **Gesamtrahmen 1,5 Mio** (Neu- & Gebrauchtfahrzeuge).

- **Stellantis:** Es gibt dort keine vergleichbare Zuordnung „Mobilität“ im Import; Stellantis-Positionen sind Lager (Neuwagen/Gebraucht). Die Empfehlung „Stellantis → Santander“ betrifft **Lagerfahrzeuge**, die bei Santander unter den **1,5-Mio-Rahmen** (Neu- & Gebraucht) fallen, **nicht** unter den 500k-Mobilität-Rahmen.

### Nutzung in der Zinsen-API

- **Report:** Die Zinsen-API kann `kreditrahmen_mobilitaet` (500k) aus der Modalitäten-DB lesen und die **Santander-Belegung nach Mobilität** ausweisen: Summe `aktueller_saldo` mit `finanzinstitut = 'Santander'` und `produkt_kategorie IN ('Mobil/Vermieter', 'Vorführer')`. So sind **Anteil (500k)** und **tatsächliche Belegung Mobilität** im Dashboard sichtbar.
- **Handlungsempfehlung Stellantis → Santander:** Sie nutzt weiterhin das **Gesamtlimit 1,5 Mio** (bzw. `ek_finanzierung_konditionen.gesamt_limit`), weil umgefinanziert werden Lagerfahrzeuge (Neu/Gebraucht), nicht Mobilität.
