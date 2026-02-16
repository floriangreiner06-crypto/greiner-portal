# Werkstatt & Aftersales — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-16

## Beschreibung

Werkstatt und Aftersales umfassen Stempeluhr/Live-Monitoring, Mechaniker-Leistung, ML-Prognosen, Gudat-Integration, Serviceberater-Dashboard, Garantie-Aufträge und -Akte, Arbeitskarte, Reparaturpotenzial, SOAP-Schnittstellen und ServiceBox-Scraper.

## Module & Dateien

### APIs
- `api/werkstatt_api.py`, `api/werkstatt_data.py` — Werkstatt-Kern
- `api/werkstatt_live_api.py` — Stempeluhr, Live-Monitoring
- `api/unfall_wissensbasis_api.py` — M4 (Checkliste, Urteile); `api/unfall_rechnungspruefung_api.py` — M1 (Aufträge, Vollständigkeitscheck)
- `api/serviceberater_api.py`, `api/serviceberater_data.py` — Serviceberater-Dashboard
- `api/garantie_auftraege_api.py` — Garantie-Aufträge
- `api/arbeitskarte_api.py` — Arbeitskarte
- `api/reparaturpotenzial_api.py` — Reparaturpotenzial
- `api/gudat_api.py`, `api/gudat_data.py` — Gudat-Integration
- `api/ml_api.py`, `api/ai_api.py` — ML/Prognosen

### Templates
- `templates/aftersales/*.html` (inkl. `unfall_wissensdatenbank.html`, `unfall_rechnungspruefung.html`, `garantie_handbuecher.html`)

### Tools / Scripts
- `tools/gudat_*.py`
- `tools/scrapers/servicebox_*.py`
- `scripts/ml/`

### Celery Tasks
- `werkstatt_leistung`, `servicebox_*`, `email_werkstatt_tagesbericht`, `ml_retrain`, `benachrichtige_serviceberater_ueberschreitungen`

## DB-Tabellen (PostgreSQL drive_portal)

- `orders`, `labours`, View `times`, `employees_history`, `absence_calendar`, `werkstatt_leistung_daily`, `delivery_notes`

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ **Workstream-Zuordnung (2026-02-12):** TEK in Workstream Controlling verschoben (Scope + CONTEXT.md, CLAUDE.md, .cursorrules angepasst).
- ✅ **Alarm-E-Mail Doppelversand (2026-02-12):** Race-Condition behoben: „INSERT first“ statt „SELECT → SEND → INSERT“. Pro Auftrag/Empfänger/Tag wird nur noch 1 E-Mail gesendet, auch bei überlappenden Celery-Läufen (z. B. 09:45 und 10:00). Siehe `docs/BUGFIX_ALARM_EMAIL_DOPPELT_TAG213.md`.
- ✅ Stempeluhr, Serviceberater, Gudat-Anbindung in Nutzung
- 🔧 ML, Garantieakte, ServiceBox je nach Projektstand
- ✅ **Versicherungs-Rechnungsprüfung:** DB + M4 (inkl. UE IWW Textbausteine gescrapt, API + UI) + M1 (Ebene 1+2); M2/M3 offen
- **Navigation:** Unfall-Rechnungsprüfung & Unfall-Wissensdatenbank unter **Service → Werkstatt** (DB-Navigation, Migration `migration_tag216_navigation_unfall.sql`) sowie im Fallback-Menü „After Sales“ → „Unfall / Versicherung“ in `base.html`.
- **UE IWW Scraper:** `scripts/imports/scrape_ue_iww.py` – Vollscrape 781 Einträge; NUL-Fix im DB-Import; Optionen `--from-json`, `--seed-only`. Export: `data/ue_iww_export.json`.
- ❌ Offene Punkte: M2/M3 (Kürzungs-Abwehr/Tracking) nicht Priorität; Fokus: vollständige/korrekte Rechnungserstellung (M1).
- ✅ **Greiner-Arbeitszeitenkatalog (2026-02-12):** Analyse & Konzept abgeschlossen. Bestandsaufnahme Locosoft labours, IST-Zeiten vs. Vorgabe-AW, Freitext-Clustering, Standort Opel vs. Hyundai, Reparaturpakete-Struktur, Top-100 Standardarbeiten-Vorschlag, DRIVE-Modul-Skizze. Siehe `docs/workstreams/werkstatt/ARBEITSZEITKATALOG_ANALYSE.md`. Kein Code deployt.
- ✅ **Ergänzungen Arbeitszeitenkatalog-Doku:** Feedback Serviceleiter (7.1), Katalog mit Referenz statt nur Pauschale (7.2), Wartungspakete/Locosoft erneut geprüft (6.1–6.4), Modell AW Gruppe vs. labours_groups geklärt (6.5), Vorgabezeiten pauschal erhöhen per SOAP (8.7).
- ❌ **Nächster Schritt (Beschluss):** Zuerst in **Locosoft sauber pflegen und einrichten**; danach **DB-Stand erneut prüfen** (z. B. labours_groups, Wartungspakete). Greiner-Katalog/DRIVE-Modul folgt nach Klärung.
- ✅ **Garantie-Handbücher Phase 1 (2026-02-16):** Handbücher & Richtlinien als Referenz umgesetzt. Ordner `docs/workstreams/werkstatt/garantie` (Sync: F:\Greiner Portal\Greiner_Portal_NEU\Server\…\garantie); Seite „Handbücher & Richtlinien“ unter Service → Garantie; PDFs werden nach Sync dort abgelegt und im Portal verlinkt (Login, sichere Auslieferung). Siehe `GARANTIE_HANDBUECHER_WISSENSBASIS_MACHBARKEIT.md`.
- ✅ **Garantie Handbücher – DB-Navigation (2026-02-16):** Navi-Punkt „Handbücher & Richtlinien“ fehlte bei aktivierter DB-Navigation; Migration `add_navigation_garantie_handbuecher.sql` eingespielt, Eintrag in `navigation_items` ergänzt; `migrate_navigation_items.py` für künftige Neuaufbauten angepasst.

## Offene Entscheidungen

- Nach Locosoft-Pflege: DB (loco_auswertung_db / Spiegel) erneut prüfen – was ist dann in labours_groups, Wartungspaketen?

---

## Neues Modul: Versicherungs-Rechnungsprüfung für Unfallschäden (Feature-Plan)

**Status:** DB-Schema + M4 + M1 (Vollständigkeitscheck inkl. Ebene 1+2) umgesetzt; M2, M3 offen.

### Kontext & Ziele

Autohaus Greiner repariert Unfallschäden und stellt Rechnungen an gegnerische Haftpflichtversicherungen. Prüfdienstleister (v.a. ControlExpert/Allianz) kürzen Rechnungen systematisch; branchenüblich werden ca. 10–35 % ungerechtfertigt gekürzt. Das Modul soll:

1. Rechnungen **vor dem Versand** auf Vollständigkeit prüfen
2. Vergessene berechtigte Positionen erkennen
3. Bei Kürzungen sofort passende **Rechtsprechung** parat haben
4. **Tracking**: Wie viel geht durch Kürzungen verloren?

### Datenquellen im Autohaus

- Werkstattaufträge aus **Locosoft** (PostgreSQL)
- Sachverständigengutachten (PDF)
- Rechnungen an Versicherungen (Locosoft oder PDF)
- Prüfberichte ControlExpert/Versicherungen (PDF, eingescannt)
- Zahlungseingänge (Bankenspiegel/MT940)

### Locosoft-Analyse M1: loco_orders / loco_labours (Stand 2026-02-11)

**Struktur**
- **loco_orders:** `number` (PK), `order_date`, `subsidiary` (1/2/3), `order_customer`, `paying_customer`, `vehicle_number`, `order_mileage`, `order_classification_flag`, `has_open_positions`, `has_closed_positions`, …
- **loco_labours:** `order_number` (FK), `order_position`, `order_position_line`, `charge_type`, `time_units`, `net_price_in_order`, `text_line`, `labour_operation_id`, `is_invoiced`, `invoice_number`, …

**Kennzeichen Unfall/Versicherungsschaden**
- **Kein** eigener Auftragstyp „Unfall“ in `order_classification_flag`. Die Flag-Werte (F, M, N, O, …) stehen für Vertriebsarten (z. B. F = Verkauf an freie Werkstätten, M = Mandanten Weiterberechnung), siehe `loco_order_classifications_def`.
- **Versicherung als Zahler:** Unfallaufträge erkennt man über **paying_customer**: Kunde in `loco_customers_suppliers` mit `family_name` z. B. „%Versicherung%“, „%Huk%“, „%Allianz%“, „ADAC Versicherungs AG“. Join: `o.paying_customer = c.customer_number AND o.subsidiary = c.subsidiary`.
- **Charge-Typen:** In `loco_labours` gibt es `charge_type` 54 und 83 (laut `loco_charge_type_descriptions`: „Reparaturkosten Versicherung Real Garant“). Treten bei Versicherungs-/Garantie-Reparaturen auf (nicht ausschließlich Unfall).
- **Freitext:** In `loco_labours.text_line` kommen vor: „Freigabe-Nummer“, „Freigabenummer“, „Schaden feststellen“, „MOTOR TEILZERLEGEN, SCHADENSFESTSTELLUNG“. Suche nach „Freigabe“, „Schaden“, „Unfall“, „Gutachten“ kann zusätzlich genutzt werden.

**Empfehlung für M1:** Unfallaufträge filtern über **paying_customer** (Versicherungs-Kunden aus Stammdaten oder Namenssuche). Positionen für Vollständigkeitscheck aus **loco_labours** (und ggf. Teile aus Locosoft parts) je Auftrag laden; `charge_type` und `text_line` helfen bei Zuordnung zu unserer Checkliste (z. B. Verbringung, Probefahrt).

**Prozess:** Gutachten kommt per PDF (Upload im Modul), Rechnung wird immer in Locosoft erstellt. M1 prüft: Gutachten-Positionen und Checkliste gegen `loco_labours` (Rechnungsstand Locosoft).

**Beispiel-Datensätze (Auszug)**

| number  | order_date  | subsidiary | order_classification_flag | order_customer | paying_customer | paying_name (join) |
|---------|-------------|------------|---------------------------|----------------|-----------------|---------------------|
| 220747  | 2026-01-12  | 2          | (leer)                    | 3007401        | 2100498         | ADAC Versicherungs AG |
| 220539  | 2025-12-23  | 2          | (leer)                    | 3008484        | 2100498         | ADAC Versicherungs AG |
| 313560  | 2025-12-16  | 3          | (leer)                    | 3004455        | 3004455         | (charge_type 83)      |
| 221269  | 2026-02-10  | 2          | F                         | 1001603        | 1001603         | (normal, freie Werkstatt) |

- Auftrag **220747:** 1 Position, viele Zeilen `text_line` (charge_type 0): Freigabe-Nummer, Mietvertragnummer, Werkstattersatz, Fahrzeugdaten – typisch Versicherung/Ersatzwagen.
- Auftrag **220539:** 19 Labours, charge_types 0 und 52; „Hyundai Mobilität“, „Freigabenummer“, „Mietvertragnummer“ – Unfall/Leihwagen-Kontext.
- Auftrag **313560:** 1 Labour mit charge_type 83, net_price_in_order 565 €, text_line „24 Monate Garantie Premium …“ – Versicherung/Garantie, nicht zwingend Unfall.

### Workstream-Zuordnung

- **Hauptbereich:** werkstatt (Aftersales/Unfallreparatur)
- **Berührungspunkte:** controlling (Zahlungseingänge, offene Forderungen), integrations (PDF-Parsing für Prüfberichte)

### Feature-Architektur (4 Module)

| Modul | Kurzbeschreibung |
|-------|------------------|
| **M1: Rechnungs-Vollständigkeitscheck** | Auftrag aus Locosoft laden → Positionen gegen Checkliste prüfen → Ampelsystem (Grün/Gelb/Rot), Warnung bei fehlenden berechtigten Positionen |
| **M2: Kürzungs-Abwehr** | Prüfbericht erfassen (PDF/Manuell) → gekürzte Positionen erkennen → BGH-Urteil + Begründung pro Position → Muster-Widerspruch generieren → Eskalation (Widerspruch → Anwalt → Klage) |
| **M3: Kürzungs-Tracking & Reporting** | Pro Versicherung: Kürzungssumme, -häufigkeit, Widerspruchserfolg; Pro Position: Kürzungshäufigkeit; Jahresverlust, Trends; Dashboard mit KPIs |
| **M4: Wissensdatenbank** | Urteile (Aktenzeichen, Datum, Kurzfassung), Zuordnung Position ↔ Urteil, Suchfunktion, pflegbar |

### Typische Kürzungspositionen (Checkliste für M1/M2)

| Position | Häufigkeit | Rechtslage |
|----------|------------|------------|
| Verbringungskosten | Sehr häufig | BGH: fast immer berechtigt |
| UPE-Aufschläge | Sehr häufig | Berechtigt bei konkreter Abrechnung |
| Beilackierung angrenzender Bauteile | Häufig | Technisch notwendig (Farbtonsicherheit) |
| Desinfektionskosten | Häufig | Strittig, oft durchsetzbar |
| Stundenverrechnungssätze („günstigere Werkstatt“) | Sehr häufig | Markenwerkstatt steht Vertragswerkstatt zu |
| Kleinersatzteile / Befestigungssätze | Häufig | Pauschale branchenüblich |
| Probefahrtkosten | Mittel | Technisch notwendig (Qualitätssicherung) |
| Reinigung, Entsorgung, Ofentrocknung | Mittel | Berechtigt / real anfallend |
| Mietwagenkosten bei Verzögerung | Bei Verzug | Werkstattrisiko beim Schädiger (BGH) |
| Unfallverhütungskosten | Selten | Arbeitssicherheit, berechtigt |

### Rechtsprechung (Wissensbasis M2/M4)

- **BGH 16.01.2024:** 5 Urteile — Versicherung muss Werkstattrechnung ungekürzt zahlen; Geschädigter trägt kein Werkstattrisiko.
- **Grundsatzurteile:** BGH VI ZR 42/73 (Werkstattrisiko), AG Dinslaken 32 C 147/22 (Nebenpositionen), BGH VI ZR 53/09 (Markenwerkstatt <3 Jahre), BGH VI ZR 267/14 (Referenzwerkstatt 20 km unzumutbar).
- **Regeln:** § 249 BGB; Werkstattrisiko beim Schädiger; ControlExpert nicht sachverständig; Markenwerkstatt bei <3 Jahre oder regelmäßiger Markenwartung.

### Externe Referenzquellen (Links/Wissensbasis)

- ZKF (zkf.de), Captain HUK (captain-huk.de), schaden.news, Kanzlei Voigt/Schleyer, CarRight.de, Stiftung Warentest, ra-kotz.de

### Prüfdienstleister

ControlExpert, CarExpert, DEKRA, SSH, HP ClaimControlling, KRUG.

### DB-Tabellen (Vorschlag, PostgreSQL drive_portal)

| Tabelle | Zweck |
|---------|--------|
| `unfall_rechnungen` | Auftragsnummer, Versicherung, Gutachten-Nr, Rechnungsbetrag, Status |
| `unfall_positionen` | Position, Betrag, Kategorie (Checkliste), in_rechnung, gekürzt |
| `unfall_kuerzungen` | Prüfbericht-ID, Position, Kürzungsbetrag, Begründung, Widerspruch_Status |
| `unfall_urteile` | Aktenzeichen, Gericht, Datum, Position_Kategorie, Kurzfassung, Volltext_Link |
| `unfall_versicherungen` | Name, Prüfdienstleister, Kürzungsstatistik |

### Priorität & Aufwand

- **Priorität:** Hoch (jede nicht-widersprochene Kürzung kostet ca. 200–1.500 €).
- **Umsetzung:** Start nach ausdrücklichem OK.

---

## Abhängigkeiten

- HR/Locosoft (Mitarbeiter), Integrations (Locosoft SOAP, ServiceBox), Infrastruktur (Celery)
