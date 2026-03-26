# Verkäufer-Zielplanung – Was ist schon da, wo packen wir es hin?

**Stand:** 2026-02  
**Zweck:** Bestandsaufnahme Planung in DRIVE + Vorschlag Einordnung des Verkäufer-Zielplanungstools (Kalenderjahr, NW/GW-Ziele).

---

## 1. Was ist in DRIVE bereits da (Planung & Verkauf)

### 1.1 Planung (Controlling / Abteilungsleiter)

| Was | URL | Dateien | Zielgruppe |
|-----|-----|---------|------------|
| **Abteilungsleiter-Planung** | `/planung/abteilungsleiter` | `routes/planung_routes.py`, `api/abteilungsleiter_planung_*.py`, `templates/planung/abteilungsleiter_*.html` | Controlling |
| **Freigabe / Gesamtplanung** | `/planung/freigabe`, `/planung/gesamtplanung` | wie oben | Geschäftsführung |
| **Gewinnplanung V2 (GW)** | `/planung/v2/` | `routes/gewinnplanung_v2_routes.py`, `templates/planung/v2/*.html` | Verkauf/Controlling |
| **KST-Ziele (Tagesstatus)** | `/controlling/kst-ziele` | `routes/controlling_routes.py`, `templates/controlling/kst_ziele.html` | Controlling |
| **Unternehmensplan (1%-Ziel)** | `/controlling/unternehmensplan` | Controlling-Routes | Controlling |

### 1.2 Verkauf – Planung & Daten

| Was | URL | Dateien | Zielgruppe |
|-----|-----|---------|------------|
| **Budget-Planung** | `/verkauf/budget`, `/verkauf/planung` | `routes/verkauf_routes.py`, `api/budget_api.py`, `templates/verkauf_budget.html` | VKL / GF |
| **Budget-Wizard (5 Fragen)** | `/verkauf/budget/wizard` | `verkauf_budget_wizard.html` | VKL / GF |
| **Lieferforecast** | `/verkauf/lieferforecast` | `verkauf_routes.py`, `verkauf_lieferforecast.html` | Verkauf |

**Bereits vorhanden für Verkäufer-Zielplanung:**

- **`api/budget_api.py`** – Route **`GET /api/budget/verkaufer/<jahr>`**: Stück und Umsatz pro Verkäufer (NW/GW) aus Locosoft `dealer_vehicles` für ein Kalenderjahr.
- **Stückzahl-Scripte:** `scripts/verkauf/stueckzahl_analyse_nach_mitarbeiter.py` – gleiche Logik für 2023/2024/2025, CSV pro Jahr + Namen aus `employees_history`; Pool Handelsgeschäft in `VERKAEUFER_HANDELSGESCHAEFT_POOL.md` (9001, 1003, 2000).

### 1.3 Navigation (base.html)

- **Controlling:** Zielplanung (1%-Ziel, KST-Ziele), Abteilungsleiter-Planung, AFA, Bankenspiegel, …
- **Verkauf:** Auftragseingang, Auslieferung, Profitabilität, **Planung** (Budget-Planung, Lieferforecast) – nur für `admin`, `geschaeftsleitung`, `verkauf_leitung`.

---

## 2. Vorschlag: Wo das Planungstool „Verkäufer-Zielplanung“ hinpacken

### 2.1 Einordnung: **Verkauf** (nicht unter /planung/)

**Begründung:**

- Verkäufer-Zielplanung ist **Verkaufsdomäne**: Verkäufer, NW/GW-Stück, Konzernziele 630/900.
- Gleiche **Zielgruppe** wie Budget-Planung: Verkaufsleitung / GF.
- **Daten:** Locosoft `dealer_vehicles` + `employees_history`; Budget-API hat bereits Verkäufer/Jahr; Stückzahl-CSV/History für 2023–2025 vorhanden.
- Unter **`/planung/`** liegen Abteilungsleiter-Planung (10 Fragen pro KST) und Gewinnplanung V2 – thematisch anders (KST/DB1), nicht Verkäufer-Stückziele.

### 2.2 Konkreter Vorschlag

| Aspekt | Vorschlag |
|--------|-----------|
| **URL** | `/verkauf/zielplanung` (alternativ: `/verkauf/verkaeufer-zielplanung`) |
| **Menü** | **Verkauf** → Bereich „Planung“ → neuer Eintrag **„Verkäufer-Zielplanung“** (unter Budget-Planung, Lieferforecast) |
| **Route** | In **`routes/verkauf_routes.py`** eine neue Route, z. B. `@verkauf_bp.route('/zielplanung')` |
| **Template** | **`templates/verkauf_zielplanung.html`** (analog zu `verkauf_budget.html` im Root von `templates/`) |
| **API** | **Neues Modul** `api/verkaeufer_zielplanung_api.py` (empfohlen), oder Erweiterung in `api/budget_api.py` |
| **Berechtigung** | Wie Budget-Planung: `current_user.portal_role in ['admin', 'geschaeftsleitung', 'verkauf_leitung']` |

### 2.3 Dateistruktur (neu bzw. erweitert)

```
routes/verkauf_routes.py          # + Route /verkauf/zielplanung
api/verkaeufer_zielplanung_api.py # neu: Stückzahl pro Jahr, Pool, Verteilung, Ziele lesen/schreiben
templates/verkauf_zielplanung.html  # neu: UI (Jahr wählen, Historie, Ziele anzeigen/bearbeiten)
docs/workstreams/verkauf/          # Konzept, Pool, CSVs 2023–2025 bereits vorhanden
```

**Optional später:**

- Tabelle `verkaufer_ziele` (Kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw) in PostgreSQL für gespeicherte Ziele und History.

### 2.4 Menü-Ergänzung (DB-Navigation)

**Nicht in base.html hardcoden.** Wenn USE_DB_NAVIGATION=true, kommt die Navigation aus der Tabelle `navigation_items`. Der Eintrag „Verkäufer-Zielplanung“ wird per Migration angelegt:

- **Migration:** `migrations/add_navigation_verkaeufer_zielplanung.sql` (INSERT unter Verkauf, order_index 9, role_restriction: admin,geschaeftsleitung,verkauf_leitung)
- **Nach Neuaufbau der DB:** `scripts/migrate_navigation_items.py` enthält den Eintrag ebenfalls.

Siehe CLAUDE.md Abschnitt „Navigation (DB-basiert)“.

---

## 3. Kurzfassung

- **Bereits da:** Abteilungsleiter-Planung, KST-Ziele, Budget-Planung, Gewinnplanung V2; Budget-API mit Verkäufer/Jahr; Stückzahl-Scripte 2023–2025 + Pool Handelsgeschäft.
- **Empfehlung:** Verkäufer-Zielplanung unter **Verkauf** einordnen: **URL** `/verkauf/zielplanung`, **Route** in `verkauf_routes.py`, **Template** `verkauf_zielplanung.html`, **API** `verkaeufer_zielplanung_api.py`, **Menü** Verkauf → Planung → „Verkäufer-Zielplanung“.

Damit bleibt Verkauf die SSOT für Verkäufer und Stückziele; die bestehenden Planungsseiten unter `/planung/` und `/controlling/` bleiben für KST/Abteilungsleiter/Unternehmensplan unverändert.
