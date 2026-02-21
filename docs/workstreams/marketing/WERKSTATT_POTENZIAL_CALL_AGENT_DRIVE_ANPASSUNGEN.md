# Werkstatt-Potenzial Call-Agent / Verschleißreparatur – DRIVE-Anpassungen

**Stand:** 2026-02-21  
**Kontext:** Spezifikation (mit Claude erarbeitet) für priorisierte Kundenliste „welche Kunden wann anrufen (Verschleiß fällig)“ und CSV-Export für Catch (Prof4net). Dieser Text gleicht den Prompt mit der **DRIVE-Arbeitsweise** und dem **aktuellen Stand** ab und hält die **Phase-1-Ergebnisse** fest.

---

## 1. Phase-1-Ergebnisse (Datenqualität Locosoft)

Queries mit **korrigierten Locosoft-Spalten** ausgeführt (Skript: `scripts/marketing/phase1_datenqualitaet_queries.py`). Locosoft read-only.

### Query 1 – km-Stand Qualität (orders, letzte 3 Jahre)

| Kennzahl | Wert |
|----------|------|
| total_orders | 43.974 |
| with_mileage | 35.059 (79,7 %) |
| unique_vehicles | 10.440 |
| vehicles_with_km | 10.396 |

### Query 2 – Fahrzeuge mit mehreren km-Messungen (5 Jahre)

| Messungen | Fahrzeuge |
|-----------|-----------|
| 1 | 3.725 |
| 2 | 1.868 |
| 3 | 1.456 |
| 4 | 995 |
| 5 | 726 |
| 6–23 | … (abfallend) |

→ Ausreichend Fahrzeuge mit ≥2 Messungen für km/Jahr-Schätzung (HIGH-Confidence). 3.725 nur mit 1 Messung (MEDIUM).

### Query 3 – Top-40 Bremsarbeiten (Hyundai + Opel, 3 Jahre)

Wichtigste text_line (Auszug): Bremsflüssigkeitswechsel/-wechseln, ENTLEERT U BEFUELLT BREMSKREISLAUF, WECHSEL DER BREMSFLÜSSIGKEIT, Bremsscheibe vorn/hinten ersetzen, Bremsbeläge vorne/hinten, BREMSBELAGBAUGRUPPE, SCHEIBENBAUGRUPPE-HINTEN BREMSE, BELAGSATZ SCHEIBENBREMSEN-VORN/HINTEN, SCHEIBE-VORDERBREMSE (LINKS/RECHTS), etc.  
→ Keywords für **bremsen_va** / **bremsen_ha** aus diesen Formulierungen ableiten (z. B. „bremsscheib“, „bremsbelag“, „bremsbelag vorn“, „vorderbremse“, „hinterradscheibe“, „hinten“).

### Query 4 – Top-40 Batterie/Zahnriemen/Steuerkette/Reifen (3 Jahre)

- **Batterie:** „Batterie ersetzen“, „Batterie prüfen und ggf.laden“, „Starterbatterie“, „Tansmitter-Batterie“, „eCall-Systembatterie“, „Batterie Funk-Fernbedienung“, „Hochspannungsbatterie“ / „Hochvolt“ (E-Auto getrennt betrachten).  
- **Zahnriemen/Steuerkette:** „Zahnriemen - Austausch“, „Nockenwelle Zahnriemen“, „Spannvorrichtung Zahnriemen“, „Zahnriemen-Umlenkrolle“, „AUSTAUSCH STEUERZAHNRIEMEN“.  
- **Reifen:** „Reifen ersetzen“ (1/2/4 Räder), „Reifen instandsetzen“, „Reifenüberwachungssystem“, „Reifendruck“, „Allwetterreifen“.  

→ Keywords für **batterie**, **zahnriemen**, **reifen** aus diesen Texten validieren; E-Auto-Batterie ggf. eigene Kategorie oder Ausschluss.

**Freigabe Phase 1:** Ergebnisse liegen vor; Keywords können aus den Top-40 abgeleitet werden.

---

## 1b. Phase 2–3 umgesetzt (2026-02-21)

- **Migration:** `migrations/add_marketing_potenzial_tables.sql` – Tabellen `repair_categories`, `repair_category_keywords`, `vehicle_km_estimates`, `vehicle_repair_scores` in drive_portal.
- **Scoring-Script:** `scripts/marketing/marketing_km_scoring.py` – liest Locosoft (Kundenfahrzeuge Opel/Hyundai), berechnet km-Schätzung und Reparatur-Scores, schreibt in Portal. Aufruf: `python scripts/marketing/marketing_km_scoring.py` (optional `--dry-run`).
- **API:** `api/marketing_potenzial_api.py` – Endpoints `/api/marketing/potenzial/categories`, `/api/marketing/potenzial/stats`, `/api/marketing/potenzial/list`, `/api/marketing/potenzial/export.csv`. Berechtigung: Feature **marketing_potenzial** (in Rechteverwaltung vergeben).
- **Navigation:** Migration `migrations/add_navigation_marketing_potenzial.sql` – Menüpunkt „Werkstatt-Potenzial“ unter Service (requires_feature: marketing_potenzial).
- **Seite:** Route `/marketing/potenzial`, Template `templates/marketing/potenzial.html` (Bootstrap 5, Filter Standort/Kategorie/Priorität/Confidence, Tabelle, CSV-Export-Button).
- **Halter/Telefon:** API und CSV-Export reichern aus Locosoft an (vehicles.owner_number → customers_suppliers, customer_com_numbers); Spalten holder_name, holder_phone in Liste und CSV.

---

## 2. Anpassungen an DRIVE-Arbeitsweise und Stand

Folgende Punkte aus dem ursprünglichen Prompt sind **nicht konform** oder veraltet und sollten so umgesetzt werden:

### 2.1 Datenbank: PostgreSQL, nicht SQLite

- **DRIVE-Hauptdatenbank** ist **PostgreSQL** (drive_portal, seit TAG 135). SQLite wird nur noch für Legacy/Altdaten genutzt.
- **Phase 2:** Neue Tabellen (vehicle_km_estimates, vehicle_repair_scores, repair_category_keywords) in **PostgreSQL** anlegen, nicht in SQLite.
- **Migration:** Unter `migrations/` als **PostgreSQL-Migration** (z. B. `migrations/add_marketing_potenzial_tables.sql`) mit Syntax für PostgreSQL: `SERIAL` statt `AUTOINCREMENT`, `TEXT`, `REAL`, `CHECK`, `REFERENCES` auf passende Portal-Tabellen oder nur interne Referenzen; keine `INSERT OR IGNORE` – stattdessen `ON CONFLICT DO NOTHING` oder separates Migrations-Script.
- **Schema-Doku:** Änderungen in `docs/DB_SCHEMA_POSTGRESQL.md` ergänzen.

### 2.2 Locosoft-Spalten (read-only)

- **orders:** Primärschlüssel ist **`number`**, nicht `order_number`. JOIN: `labours.order_number = orders.number`. Felder: `vehicle_number`, `order_date`, `order_mileage`, `subsidiary`, `order_customer`.
- **vehicles:** Fahrzeug-PK ist **`internal_number`**. JOIN: `orders.vehicle_number = vehicles.internal_number`. Felder: `owner_number`, `make_number`, `first_registration_date`, `mileage_km`, `odometer_reading_date`, `next_service_date`, `next_service_km`, `subsidiary`; kein `vehicle_number` als Spaltenname.
- **customers_suppliers:** Keine Spalten `name1`/`name2`. Verwenden: **`first_name`**, **`family_name`** (ggf. `name_prefix`, `name_postfix`). **Telefon/E-Mail** stehen nicht direkt in customers_suppliers, sondern in **`customer_com_numbers`** (customer_number, com_type, phone_number, address für E-Mail etc.). Für „Halter + Telefonnummer“ also JOIN auf customer_com_numbers (und ggf. preferred_com_number_type beim Kunden).
- **makes:** `make_number`, `description`. Opel = **40**, Hyundai = **27** (bereits in Potenzialanalyse bestätigt).

### 2.3 Navigation: DB-basiert, nicht base.html

- **Menüpunkte** kommen aus der Tabelle **`navigation_items`** (PostgreSQL), nicht aus hardcodierten Einträgen in `base.html`. Vorgehen: Migration anlegen, z. B. `migrations/add_navigation_marketing_potenzial.sql` mit `INSERT INTO navigation_items (parent_id, label, url, icon, order_index, requires_feature, role_restriction, ...)`. Parent = ID des Menüpunkts „Marketing“ (falls vorhanden) oder passender Oberpunkt. Optional `scripts/migrate_navigation_items.py` ergänzen. Siehe CLAUDE.md Abschnitt „Navigation (DB-basiert)“.

### 2.4 Weitere technische Punkte

- **Bootstrap:** Projekt nutzt **Bootstrap 5** (laut CLAUDE.md); Template „konsistent mit anderen DRIVE-Modulen“ also Bootstrap 5.
- **Celery:** Task in `celery_app/tasks.py` anlegen; Konfiguration in `celery_app/celery_config.py` / Beat, falls Berechnung periodisch laufen soll.
- **API:** Blueprint in `app.py` registrieren; Routen unter z. B. `/api/marketing/` oder unter einem bestehenden Marketing-Blueprint.
- **DSGVO:** Keine echten Kundendaten in Logs; Export/CSV nur für berechtigte Nutzer (Feature/ Rolle prüfen).

---

## 3. Zusammenfassung: Was bei Phase 2–6 zu beachten ist

| Phase | Anpassung |
|-------|-----------|
| **2** | PostgreSQL-Migration in `migrations/`, Tabellen in **drive_portal**; Spalten- und Datentypen PostgreSQL; Keywords nach Phase-1-Ergebnissen einpflegen. |
| **3** | Script liest aus **Locosoft** (read-only) und schreibt in **PostgreSQL** (drive_portal); Verbindung über `api.db_utils` (get_db, locosoft_session). Kunden-/Telefonabfrage über customers_suppliers + customer_com_numbers. |
| **4** | API mit Filter (subsidiary, category_id, priority, confidence); JOIN vehicle_repair_scores + vehicle_km_estimates + Locosoft-Daten (vehicles, customers_suppliers, customer_com_numbers) – Locosoft read-only, Halterdaten für Anzeige/Export aus Locosoft lesen. |
| **5** | Template Bootstrap 5; Pagination und Export-Button wie spezifiziert. |
| **6** | Blueprint in app.py; **Navigation nur über Migration** (navigation_items), kein direkter Eintrag in base.html. |

---

## 4. Dateien / Referenzen

- **Phase-1-Queries (korrigiert):** `scripts/marketing/phase1_datenqualitaet_queries.py`
- **Locosoft-Schema:** `docs/DB_SCHEMA_LOCOSOFT.md`
- **PostgreSQL-Schema (Portal):** `docs/DB_SCHEMA_POSTGRESQL.md`
- **Navigation:** CLAUDE.md Abschnitt „Navigation (DB-basiert)“, `migrations/add_navigation_*.sql`, `scripts/migrate_navigation_items.py`
- **Reparaturpotenzial (bestehend):** `api/reparaturpotenzial_api.py` – regelbasiert nach km/Alter; ggf. Abgrenzung oder Wiederverwendung von Logik (Keywords, Schwellen).

Wenn du Phase 2 (Migration + Tabellen) umsetzen willst, zuerst fachliche Freigabe zu den Keywords/Kategorien aus Phase 1; dann Migration und Script wie oben angepasst bauen.
