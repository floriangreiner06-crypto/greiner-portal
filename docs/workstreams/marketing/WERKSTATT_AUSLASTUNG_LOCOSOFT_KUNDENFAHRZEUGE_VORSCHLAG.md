# Werkstattauslastung: Potenzialanalyse Locosoft-Kundenfahrzeuge

**Stand:** 2026-02-21  
**Kontext:** Werkstattauslastung nicht zufriedenstellend; Potenziale in Locosoft-Kundenfahrzeugen erforschen.  
**Auftrag:** Kein Code – zuerst Internet-Recherche, Anregungen, Vorschlag.

**Ergänzung (2026-02-21):** HU/AU-Ansprache läuft über **Veact**; Marketing-Modul **Catch (Prof4net)** wird genutzt. ML/Bedrock-Potenziale und die **richtige Inspektion** (Opel/Hyundai) sind in [ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md](ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md) beschrieben.

**Locosoft-Analyse (2026-02-21):** Erstes Auswertungsskript läuft – siehe Abschnitt [„Ergebnis Locosoft-Analyse“](#ergebnis-locosoft-analyse-2026-02-21) unten. Skript: `scripts/marketing_locosoft_potenzial_analyse.py`.

---

## 1. Kurzfassung Internet-Recherche

### 1.1 Wo das Potenz liegt

- **Branche:** Ein erheblicher Teil des Umsatzpotenzials geht verloren, weil Kunden HU, Inspektion oder Reifen woanders machen. Mit gezieltem Service-Marketing lassen sich 60–70 % der Stammkunden aktivieren (vs. nur ~20 % ohne aktive Ansprache).
- **HU (Hauptuntersuchung)** gilt als zentraler „Kundenmagnet“: viele Kunden erwarten eine individuelle Erinnerung; HU wird oft mit Reparatur/Wartung kombiniert → Zusatzumsatz.
- **Nur ca. 11 %** der Wartungsaufträge entstehen durch aktive Hinweise der Werkstatt – der Rest durch Eigeninitiative der Kunden. Proaktive Erinnerungen werden von Kunden als hilfreich eingestuft.
- **Werkstatt-Termine** werden heute noch überwiegend per Telefon vereinbart; digitale Kanäle (E-Mail, ggf. WhatsApp) werden von Kunden gewünscht (E-Mail ~85 %, Telefon ~44 %) und können Auslastung und Planbarkeit verbessern.

### 1.2 Typische Hebel (ohne Anspruch auf Vollständigkeit)

| Hebel | Kurzbeschreibung |
|-------|------------------|
| **HU/AU fällig** | Fälligkeit aus Erstzulassung oder letzter HU ableiten; gezielte Erinnerung (E-Mail/SMS/WhatsApp/Brief). |
| **Inspektion fällig** | Nächste Inspektion (Datum/Kilometer) – aus Fahrzeugstamm oder letztem Service. |
| **Lange kein Werkstattbesuch** | „Lost Customers“: letzter Auftrag z.B. > 12/18/24 Monate – Reaktivierungskampagne. |
| **Saisonale Themen** | Reifen (Sommer/Winter), Klimaanlage, Bremsen – gefiltert nach Fahrzeugalter/Kilometerstand. |
| **Zusatzleistungen** | Bei kleineren Schäden (Kratzer, Delle) wird oft nicht aktiv angeboten – Potenzial für Aufklärung/Kampagnen. |
| **Datenqualität** | Eine saubere Kunden-/Fahrzeugstamm-Pflege und Abgleich mit tatsächlichen Aufträgen verbessert alle Auswertungen. |

### 1.3 Quellen (Auswahl)

- DAT/autohaus.de: HU als Kundenmagnet, Erwartung an Erinnerungen, Werkstattbesuch Kontakt und Potenzial.
- Studien: Kunden wünschen häufigere Erinnerungen; Kommunikation bevorzugt E-Mail/Telefon.
- McKinsey: Fixed-Cost-Absorption im Service; geringe Verbesserungen können große Hebel bringen.
- DriveSure/MOTOR: Auslastung durch Analytics (Kapazität, Durchlaufzeiten, Kundensegmentierung).

---

## 2. Was in Locosoft vorhanden ist (relevante Tabellen)

Die folgenden Daten in der **Locosoft-PostgreSQL-Datenbank** (read-only für DRIVE) eignen sich für eine reine **Potenzialforschung** (Auswertungen, Listen, Kennzahlen – ohne sofortige Kampagnen-Automatik).

### 2.1 Fahrzeuge: `vehicles` (~58.561 Zeilen)

- **Kundenfahrzeuge:** `is_customer_vehicle = true` (Abgrenzung zu Händlerfahrzeugen).
- **Fälligkeiten (am Fahrzeug geführt):**
  - `next_general_inspection_date` (HU)
  - `next_emission_test_date` (AU)
  - `next_service_date`, `next_service_km` / `next_service_miles`
  - optional: `next_rust_inspection_date`, `next_exceptional_inspection_da`
- **Alter/Laufleistung:** `first_registration_date`, `mileage_km`, `odometer_reading_date`, `production_year`.
- **Zuordnung:** `owner_number` → Verknüpfung zu `customers_suppliers` (Kunde/Halter).

### 2.2 Kunden: `customers_suppliers` (~53.524 Zeilen)

- Adresse, Kontakt, `last_contact`; ggf. `service_assistant_employee_no` (Serviceberater).
- Für Kampagnen später: Kontaktkanäle (E-Mail/Telefon) – abhängig von DSGVO und vorhandenen Feldern.

### 2.3 Werkstatt-Historie: `orders` + `labours` (+ `invoices`)

- **orders:** `vehicle_number`, `order_customer`, `order_date`, `order_mileage`, `subsidiary`.
- **labours:** Arbeitspositionen pro Auftrag (Art der Arbeit, ggf. über `labours_master` interpretierbar).
- Daraus ableitbar:
  - **Letzter Werkstattbesuch** pro Fahrzeug (max. `order_date` je `vehicle_number`).
  - **Zeitspanne seit letztem Besuch** (z.B. „> 12 Monate“ = Reaktivierungspotenzial).
  - Optional: grobe Zuordnung „Inspektion vs. Reparatur“ über Labour-Texte/Gruppen (aufwändiger).

### 2.4 Reifen: `tire_storage` (~4.788 Zeilen)

- Reifenlager pro Fahrzeug – sinnvoll für Reifen-/Saison-Kampagnen (Sommer/Winter), sofern VIN/Fahrzeug verknüpft.

### 2.5 Standorte

- `subsidiary` in vehicles/orders (1 = Deggendorf Opel, 2 = Deggendorf Hyundai, 3 = Landau) – Auswertung nach Werkstatt/Standort möglich.

---

## 3. Vorschlag: Potenzial-Analysen (ohne Code, nur Konzept)

Ziel: **Konkrete, priorisierte Auswertungen** definieren, die ihr in Locosoft (oder später in DRIVE auf Basis von Locosoft-Daten) nutzen könnt – um zu verstehen, *wo* das meiste Potenz liegt, bevor ihr Kampagnen oder Erinnerungsläufe plant.

### 3.1 Analyse 1: HU/AU-Fälligkeit (Kundenfahrzeuge) — bei euch über Veact

**Hinweis:** HU/AU wird bei euch über **Veact** angesprochen. Die folgende Analyse kann trotzdem zur **Mengenplanung** oder zum Abgleich (wie viele Fahrzeuge sind HU/AU-relevant?) genutzt werden; Kampagnen laufen weiter über Veact.

- **Filter:** `vehicles.is_customer_vehicle = true`, gültige `owner_number`, Standort optional.
- **Fälligkeit:**  
  - Entweder Nutzung von `next_general_inspection_date` / `next_emission_test_date`,  
  - oder Schätzung aus `first_registration_date` (z.B. HU alle 2 Jahre), falls Datumsfelder leer.
- **Ausgabe (Beispiele):**  
  - Anzahl Fahrzeuge mit HU fällig in 0–1 Monat, 1–3 Monaten, 3–6 Monaten.  
  - Liste: Fahrzeug (Kennzeichen/VIN), Halter, Fälligkeit, letzter Auftrag (aus `orders`).  
- **Nutzen:** Abschätzung, wie viele „HU-Erinnerungen“ überhaupt möglich sind; Priorisierung nach „bald fällig“.

### 3.2 Analyse 2: „Lange kein Werkstattbesuch“ (Reaktivierung)

- **Definition:** Kundenfahrzeuge, bei denen der **letzte Auftrag** (max. `order_date` in `orders` für dieses `vehicle_number`) z.B. **> 12 Monate** oder **> 18/24 Monate** zurückliegt.
- **Verknüpfung:** `vehicles` → `orders` (über `vehicle_number`), nur Service-Aufträge (kein reiner Verkauf); Abgrenzung evtl. über `order_classification_flag` oder Auftragstyp, sofern in Locosoft gepflegt.
- **Ausgabe:** Anzahl betroffener Fahrzeuge pro Standort; Liste mit Halter, letztem Besuch, Fahrzeugalter/Kilometerstand.
- **Nutzen:** Größe des „Lost Customer“-Potenzials; Grundlage für Reaktivierungskampagnen (E-Mail/Post/Telefon).

### 3.3 Analyse 3: Nächste Inspektion (Datum/Kilometer)

- **Daten:** `vehicles.next_service_date`, `next_service_km`, aktueller `mileage_km` (und `odometer_reading_date`).
- **Logik:** Fahrzeuge, bei denen `next_service_date` in den nächsten 1–3 Monaten liegt oder `next_service_km` bereits erreicht/überschritten (bei gepflegtem Kilometerstand).
- **Ausgabe:** Anzahl und Liste (Fahrzeug, Halter, geplantes Datum/km, letzter Auftrag).
- **Nutzen:** Inspektions-Erinnerungen und bessere Auslastungsplanung.

### 3.4 Analyse 4: Reifen/Saison (optional)

- **Daten:** `tire_storage` (Fahrzeugzuordnung), ggf. `vehicles` (Alter, Standort).
- **Idee:** Fahrzeuge identifizieren, die für Reifenwechsel/Neureifen (Sommer/Winter) in Frage kommen – z.B. alter Reifenbestand oder hoher Kilometerstand ohne aktuellen Reifeneintrag.
- **Nutzen:** Saisonale Kampagnen (Reifen, Bremsen-Check), bessere Auslastung in typischen Reifenmonaten.

### 3.5 Analyse 5: Datenqualität und Abdeckung

- **Fragen:** Wie viele Kundenfahrzeuge haben gepflegte `next_general_inspection_date` / `next_service_date` / `next_service_km`? Wie viele haben mindestens einen Auftrag in `orders` (Werkstatt-Historie)?
- **Ausgabe:** Anteile (in %) und absolute Zahlen; Hinweis auf Lücken für HU-Schätzung aus `first_registration_date`.
- **Nutzen:** Entscheidung, ob zuerst Stammdaten in Locosoft nachgepflegt werden sollten, damit Kampagnen sauber ankommen.

---

## 4. Empfohlene Reihenfolge und nächste Schritte

1. **Datenqualität prüfen (Analyse 5)**  
   Kurz in Locosoft (oder per SQL auf read-only Kopie) prüfen: Wie vollständig sind HU/Inspektion/Datum und die Verknüpfung Fahrzeug → letzter Auftrag? Das bestimmt, welche Analysen sofort sinnvoll sind.

2. **HU/AU-Potenzial quantifizieren (Analyse 1)**  
   Größtes und meistgenanntes Hebelthema; wenig Abhängigkeit von komplexen Labour-Auswertungen.

3. **Reaktivierungspotenzial „lange kein Besuch“ (Analyse 2)**  
   Zeigt, wie viele Kunden ihr mit gezielten Kampagnen zurückholen könnt.

4. **Inspektion (Analyse 3)** und optional **Reifen (Analyse 4)**  
   Sobald die Felder in Locosoft verlässlich genug sind.

5. **Erst danach:** Entscheidung, ob und wo DRIVE unterstützen soll (z.B. Report „Service-Potenzial“, Export für E-Mail/WhatsApp, oder nur Dokumentation der Auswertungslogik für Locosoft/Excel).

---

## 5. Abgrenzung und Hinweise

- **DSGVO / Werbekommunikation:** Listen für Ansprache (E-Mail, Telefon, WhatsApp) müssen rechtskonform sein (Einwilligung, Widerspruch, Zweck). Die hier beschriebenen Analysen sind **reine Potenzialforschung** („wie viele könnten wir ansprechen?“); die konkrete Kampagnen-Umsetzung gehört in Marketing/Recht.
- **Locosoft als Quelle:** Alle Daten kommen aus Locosoft (read-only). Änderungen an Stammdaten (z.B. nächste HU/Inspektion) erfolgen in Locosoft; DRIVE würde nur lesen und auswerten.
- **Werkstatt-Workstream:** Inhaltlich schließt das an Werkstatt (Reparaturpotenzial, Serviceberater, Auslastung) und an **Integrations** (WhatsApp für Kundenansprache) an. Der Vorschlag liegt im Workstream **Marketing**, weil es um Kampagnen-Potenzial und Kundenansprache geht.

---

## 6. Zusammenfassung

- **Internet:** HU-Erinnerung und proaktive Service-Ansprache haben hohes Potenzial; viele Kunden erwarten genau das. „Lange kein Besuch“ und Inspektion/Reifen sind weitere Hebel.
- **Locosoft:** Kundenfahrzeuge (`vehicles`), Fälligkeiten (HU, AU, Inspektion), Halter (`customers_suppliers`) und Werkstatt-Historie (`orders`/`labours`) sind vorhanden und für Potenzialanalysen nutzbar.
- **Vorschlag:** Zuerst Datenqualität prüfen, dann nacheinander HU/AU-Potenzial, Reaktivierung (lange kein Besuch), Inspektion und optional Reifen auswerten – alles konzeptionell/als Auswertung, **ohne Code**. Danach entscheiden, ob DRIVE Reports, Exporte oder Kampagnen-Anbindung (z.B. WhatsApp/E-Mail) umgesetzt werden.

---

## Ergebnis Locosoft-Analyse (2026-02-21)

Ausführung: `python3 scripts/marketing_locosoft_potenzial_analyse.py` (Locosoft read-only).

### Analyse 5: Datenqualität

| Kennzahl | Wert | Anteil |
|----------|------|--------|
| Kundenfahrzeuge (mit Halter) | 58.509 | 100 % |
| next_general_inspection_date (HU) | 41.443 | 70,8 % |
| next_emission_test_date (AU) | 36.196 | 61,9 % |
| next_service_date | 13.620 | 23,3 % |
| next_service_km > 0 | 5.074 | 8,7 % |
| mileage_km > 0 | 52.821 | 90,3 % |
| first_registration_date | 57.268 | 97,9 % |
| Mind. 1 Werkstatt-Auftrag (Rechnung) | 8.851 | 15,1 % |

**Fazit:** HU/AU-Felder relativ gut gepflegt; Inspektion (next_service_date/km) schwach – nur 23 % / 9 %. Viele Kundenfahrzeuge haben noch nie einen Werkstatt-Auftrag in der Auswertung (nur 15 % mit mind. 1 Rechnung). „Betrieb 0“ = subsidiary 0 (ohne Zuordnung).

### Analyse 1: HU-Potenzial

- **HU-Datum gepflegt:** Fällig 0–1 Monat: 36.528 | 1–3 Monate: 500 | 3–6 Monate: 712. (Hinweis: 0–1 Monat enthält vermutlich viele bereits überfällige Datumsangaben – für Veact-Mengenplanung prüfen.)
- **Ohne HU-Datum, EZ mind. 2 Jahre:** 15.854 Fahrzeuge (Nachpflege-Potenzial in Locosoft).

### Analyse 2: Reaktivierung (lange kein Werkstattbesuch)

| Standort | > 12 Monate | > 18 Monate | > 24 Monate |
|----------|-------------|-------------|-------------|
| Betrieb 0 (ohne/offen) | 44.968 | 44.875 | 44.812 |
| DEG Opel | 4.381 | 3.867 | 3.301 |
| HYU Hyundai | 1.703 | 1.477 | 1.282 |
| LAN | 1.872 | 1.617 | 1.312 |

Reaktivierungspotenzial pro Werkstatt (DEG/HYU/LAN) damit grob 1.700–4.400 Fahrzeuge je Standort (> 12 Monate).

### Stichprobe Inspektionserkennung (Opel/Hyundai)

- **Hyundai:** Klar erkennbar: `labour_operation_id` = „INSP“ oder „ZI“ (Zwischeninspektion); `text_line` z. B. „Inspektion nach 2 Jahren“, „Inspektion nach 30000 Kilometer“, „Inspektion nach 60.000 km“. Eindeutige Zuordnung Inspektion 1/2/3 bzw. 15k/30k/60k über text_line oder INSP möglich.
- **Opel:** In der Stichprobe (letzte 2 Jahre) nur wenige Einträge („falsch Opel“, evtl. Schreibweise in `makes.description`); Opel-Inspektionstypen ggf. mit anderem make_number oder text_line-Muster prüfen.

**Makes für Inspektion:** Opel = `make_number` **40**, Hyundai = **27** („falsch Opel 40“ = make_number 1, Fehlpflege). Stichprobe filtert auf 40 und 27; in den letzten 2 Jahren erscheinen in den Top-40 nur Hyundai-Inspektion (Opel evtl. anderes text_line-Muster, z. B. „Service“/„Wartung“ ohne „Inspektion“).

### Analyse 3: Nächste Inspektion (next_service_date / next_service_km)

| Kennzahl | Wert |
|----------|------|
| next_service_date fällig 0–1 Monat | 11.014 |
| next_service_date fällig 1–3 Monate | 459 |
| next_service_date fällig 3–6 Monate | 727 |
| next_service_km bereits erreicht/überschritten | 623 |

Nur 23 % der Kundenfahrzeuge haben next_service_date gepflegt – Inspektions-Potenzial ist damit begrenzt auf diese Menge; Nachpflege in Locosoft würde die Basis vergrößern.

Nächster Schritt Inspektion: Regelwerk „nächste Inspektion“ für Hyundai (INSP/ZI + text_line) und für Opel (make_number 40, text_line-Muster) ableitbar; ggf. Bedrock-Klassifikation für text_line (siehe ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md).

### Analyse 4: Reifen / Kundenräder (Locosoft PostgreSQL)

**Kundenräder und Reifen** werden bei euch eingelagert und in Locosoft verwaltet. Die Locosoft-PostgreSQL-Datenbank enthält diese Informationen.

| Tabelle | Zeilen (ca.) | Inhalt |
|---------|----------------|--------|
| **tire_storage** | ~4.819 | Einlagerungs-**Fälle** pro Kunde/Fahrzeug: `case_number`, `customer_number`, `vehicle_number`, `order_number`, `start_date`, `scheduled_end_date`, `is_historic`, `is_planned`, `note`, `price`, `pressure_front/rear`, `torque` |
| **tire_storage_wheels** | ~19.302 | **Einzelräder/Reifen** pro Fall: Verknüpfung über `case_number`; Felder u. a. `tire_dimension`, `rim_description`, `product_name`, `manufacturer`, `tire_tread_depth`, `wheel_position`, `bin_location`, `is_runflat`, `has_rdks` |
| **tire_storage_accessories** | (optional) | Zubehör pro Fall |

**Abfrage (2026-02-21):**
- 4.819 Fälle, davon 4.819 mit `customer_number`, 4.780 mit `vehicle_number`, 1.365 mit `order_number`.
- 4.054 Fälle als `is_historic`, 9 als `is_planned`.
- Verteilung nach Standort (Fahrzeug-Subidiary): Betrieb 0: 352 | DEG (1): 2.066 | HYU (2): 1.606 | LAN (3): 756.
- Stichprobe: pro Fall typisch 4 Räder (`tire_storage_wheels`), `start_date` / `scheduled_end_date` für Einlagerungszeitraum.

**Nutzen für Potenzialanalyse:** Fahrzeuge mit aktiver Reifeneinlagerung (`tire_storage` mit `vehicle_number`, ggf. `is_historic = false` oder `scheduled_end_date` in der Zukunft) können für Reifenwechsel-Saison (Sommer/Winter) oder Abhol-Ansprache genutzt werden; oder Kunden ohne Einlagerung mit hohem km-Stand/Alter für Neureifen-Kampagnen.
