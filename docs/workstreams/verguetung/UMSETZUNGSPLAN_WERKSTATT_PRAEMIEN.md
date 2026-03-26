# Umsetzungsplan: Werkstatt-Prämiensystem

**Workstream:** verguetung  
**Stand:** 2026-02-13  
**Konzept-Excel:** `docs/workstreams/verguetung/2025-02-13_Prämienkonzept_Werkstatt.xlsx`

---

## 1. Konzept aus der Excel (Zusammenfassung)

### 1.1 Rollen / Funktionen
| Funktion              | Prämienstufe (Beispiel aus Excel) |
|-----------------------|-----------------------------------|
| Werkstattleiter       | wie Mechaniker (100€/150€)        |
| Stellv. Werkstattl.   | wie Mechaniker                    |
| Mechaniker            | Stufe 1: 50/100/150€ (je KPI)     |
| Azubi (1. Jahr)       | 25/50/75€, niedrigere Schwellen  |
| Azubi (3. Jahr)       | höhere Schwellen als 1. Jahr      |

**Ausschluss:** z. B. „> Langzeitkrank“ (Anmerkung) → Produktivitätsfaktor 0 oder expliziter Flag.

### 1.2 Drei KPIs und Stufen (aus Excel)

| KPI             | Formel (Team)                        | Entscheidend       | ZIEL-Stufen (Beispiel) | Prämie (Beispiel)     |
|-----------------|--------------------------------------|--------------------|------------------------|------------------------|
| **Produktivität** | Team: Σ Produktive Std / Σ Verfügbare Std | **Team-KPI**       | Stufe 1: 80%           | 100€ / 150€ / 75€ Azubi (pro MA) |
| **Leistungsgrad** | Team: Σ Abgerechnete Std / Σ Produktive Std | **Team-KPI**       | Stufe 1: 95%, 80%      | 100€ / 150€ / 75€ (pro MA)      |
| **Effektivität**  | Team: Σ Abgerechnete Std / Σ Vorgabe | **Team-KPI**       | Stufe 1: 85%, 70%      | 100€ / 75€ / 0€ (pro MA)        |

**Wichtig:** Die Prämie wird **pro Mitarbeiter** ausgezahlt, aber **Stufe und Betrag** werden ausschließlich aus den **Team-KPIs** (nicht aus Einzelwerten) bestimmt. Alle Teammitglieder erhalten dieselbe Stufe je KPI.

- **Verfügbare Anwesenheitsstunden** = Anwesenheitsstunden gesamt − Fehlstunden (evtl. × Produktivitätsfaktor).
- **Produktive Stunden** = aus Stempeluhr (`times`, type=2), Aufteilung **extern** / **intern** über `labours.charge_type` bzw. `labour_type` (I = intern).
- **Abgerechnete Stunden** = aus `labours` (is_invoiced, time_units), gleiche Aufteilung extern/intern.
- Einheit in Excel teils in 10-Minuten (AW) oder Stunden: **noch klären** (z. B. 1805 → 300,8 h wenn 10-Min).

### 1.3 Prämienbeträge (Konzept)
- Mechaniker: 50€ / 100€ / 150€ pro Stufe (je KPI).
- Azubi: 25€ / 50€ / 75€ pro Stufe.
- Monatliche Team-Berechnung, dann Zuordnung je Mitarbeiter nach Gruppe.

---

## 2. Vorhandene Daten (Bestandsaufnahme)

### 2.1 Locosoft PostgreSQL (10.80.80.8, loco_auswertung_db)

| Tabelle / View   | Inhalt für Prämien |
|------------------|--------------------|
| **times**        | Stempelzeiten: `start_time`, `end_time`, `duration_minutes`, `type` (1=Anwesenheit, 2=produktiv), `employee_number`, `order_number`, `order_position`, `order_position_line`. **Nutzung:** Anwesenheitsstunden, Produktive Stunden (type=2). |
| **labours**      | Arbeitspositionen: `time_units` (AW/Vorgabe), `mechanic_no`, `is_invoiced`, `order_number`, `charge_type`, `labour_type` (I=intern). **Nutzung:** Abgerechnete Stunden (intern/extern), Vorgabe für Effektivität. |
| **orders**       | `order_date`, `subsidiary`, Auftragsbezug. |
| **absence_calendar** | `employee_number`, `date`, `reason`, `type`, `time_from`, `time_to`. **Nutzung:** Fehlstunden pro MA/Monat. |
| **employees_history** | `employee_number`, `name`, `subsidiary`, `mechanic_number`, `productivity_factor`, `leave_date`. **Nutzung:** Stammdaten, Zuordnung Mechaniker, Produktivitätsfaktor. |
| **employees_worktimes** | `employee_number`, `dayofweek`, `work_duration`, `validity_date`. **Nutzung:** Soll-Anwesenheitsstunden (verfügbar) pro Tag/Woche. |

**Zugriff im Portal:** `api.db_utils.locosoft_session()` / `get_locosoft_connection()`; alle Werkstatt-Queries laufen gegen Locosoft (nicht gegen drive_portal-Spiegel).

### 2.2 PostgreSQL drive_portal (127.0.0.1)

| Tabelle           | Relevanz Prämien |
|-------------------|------------------|
| **employees**     | HR-Stammdaten (Urlaubsplaner); ggf. Zuordnung MA → „Funktion“ (Werkstattleiter / Mechaniker / Azubi) für Prämienstufe, falls nicht in Locosoft. |
| **loco_***        | Spiegel von Locosoft (loco_times, loco_orders, …); aktuell für Prämien **nicht** genutzt, Werkstatt-Code nutzt Locosoft direkt. |

### 2.3 Vorhandener Code (Werkstatt-KPIs)

- **api/werkstatt_data.py:**  
  - `get_anwesenheit_rohdaten(von, bis)` → Anwesenheit aus `times` (type=1).  
  - Stempelanteil / produktive Zeiten aus `times` (type=2).  
  - `get_aw_verrechnet(von, bis)` → AW/Umsatz aus `labours` + `times`.  
- **api/werkstatt_live_api.py:**  
  - Anwesenheit/Stempelungen pro Tag, Mechaniker-Liste, `absence_calendar`.  
- **docs/sql/** und **docs/BERECHNUNG_WERKSTATT_KPIS_VOLLSTAENDIG_TAG196.md:**  
  - KPI-Logik (St-Anteil, Anwesenheit, AW) – teils mit bekannten Abweichungen (Doku „ZU ÜBERPRÜFEN“).

### 2.4 Lücken / Klärungen

| Thema | Status | Handlung |
|-------|--------|----------|
| **MA → Funktion (Werkstattleiter / Mechaniker / Azubi 1./3.)** | Unklar | Entweder Locosoft (employees_history, Gruppe) oder drive_portal (employees/HR) definieren; Mapping für Prämienstufe und Beträge. |
| **Einheit Stunden** | Unklar | Excel: „1805“ Anwesenheitsstunden – 10-Min-Einheiten oder Dezimalstunden? Mit Fachbereich klären; einheitlich in DB und Berechnung. |
| **Stufen-Schwellen pro Gruppe** | Konzept in Excel | In `praemien_config` abbilden (Schwellen %, Beträge €). |
| **Intern/Extern** | Vorhanden | `labours.labour_type` = 'I' = intern; sonst extern. Bereits in werkstatt_data genutzt. |
| **Monatsbezug** | Definiert | Kalendermonat; Abrechnungslauf z. B. Monatsende + X Tage. |

---

## 3. Phasierter Umsetzungsplan

### Phase 1: Konzept & Datenabgleich (ohne Code)
- [ ] **1.1** Excel-Formeln und Stufen (%, €) mit Fachbereich final abstimmen; Einheit (10-Min vs. Stunden) festlegen.
- [ ] **1.2** Zuordnung Mitarbeiter → Funktion (Werkstattleiter/Mechaniker/Azubi 1./3.) klären (Locosoft vs. HR).
- [ ] **1.3** Kurzes SQL/Skript: für einen Testmonat aus Locosoft auslesen: pro MA Anwesenheit, Produktiv (extern/intern), Abgerechnet (extern/intern), Fehlstunden; mit Excel-Beispiel abgleichen.

### Phase 2: DB-Schema (drive_portal)
- [ ] **2.1** Tabelle **praemien_config**:  
  - KPI (Produktivität/Leistungsgrad/Effektivität), Gruppenkennung (Mechaniker/Azubi_1/Azubi_3/…), Stufe (1/2/3), Schwellwert_untergrenze (%), Prämienbetrag_EUR, gültig_von, gültig_bis.
- [ ] **2.2** Tabelle **praemien_berechnungen**:  
  - Monat (Jahr/Monat), employee_number, subsidiary, KPI-Werte (Produktivität/Leistungsgrad/Effektivität), erreichte Stufe je KPI, Prämienbetrag je KPI, Summe, Berechnungszeitpunkt, optional Rohdaten (Stunden) für Nachvollzug.
- [ ] **2.3** Migration anlegen, in DB_SCHEMA_POSTGRESQL.md eintragen.

### Phase 3: API & Berechnungslogik
- [ ] **3.1** **api/praemien_api.py** anlegen:  
  - Konfiguration lesen/schreiben (praemien_config), Berechnung für einen Monat (Lesen aus Locosoft: times, labours, absence_calendar, employees_worktimes, employees_history).  
  - Ausgabe: pro MA Kennzahlen + Stufe + Prämie; optional Team-Aggregation für Stufenlogik (wenn Stufe teambezogen).
- [ ] **3.2** Formeln aus Excel 1:1 umsetzen (Produktivität, Leistungsgrad, Effektivität); Stufenlogik aus praemien_config.
- [ ] **3.3** Einheiten konsistent (Stunden oder 10-Min) durchziehen; Fehlstunden aus absence_calendar (ggf. reason/type für „bezahlt/unbezahlt“).

### Phase 4: Celery & Abrechnungslauf
- [ ] **4.1** Task **monatliche_werkstatt_praemien_berechnung** (z. B. 1. des Folgemonats oder nach Abgleich mit Buchhaltung):  
  - Ruft Praemien-API für Vormonat auf, schreibt in **praemien_berechnungen**.
- [ ] **4.2** Optional: E-Mail/Report an Verantwortliche; keine Doppelberechnung (idempotent pro Monat/MA).

### Phase 5: Oberfläche & Reporting
- [ ] **5.1** Route (z. B. unter `/verguetung/` oder `/verguetung/werkstatt-praemien`), Berechtigung (Feature „verguetung“ bzw. Werkstatt-Prämien).
- [ ] **5.2** Template **templates/verguetung/werkstatt_praemien.html**:  
  - Monat wählen, Tabelle: MA, Kennzahlen, Stufen, Prämien; Summe; optional Export CSV/Excel.
- [ ] **5.3** Config-UI (praemien_config) optional später (z. B. Admin); initial reicht DB-Pflege oder Script.

### Phase 6: Dokumentation & Abnahme
- [ ] **6.1** CONTEXT.md (verguetung) aktualisieren: praemien_api.py, Tabellen, Task, Template.
- [ ] **6.2** Kurze Testanleitung: einen Monat durchspielen, mit Excel abgleichen; Abnahme mit Fachbereich.

---

## 4. Abhängigkeiten

- **werkstatt:** Nutzung von times, labours, orders, absence_calendar, employees_history, employees_worktimes (Locosoft); keine Änderung an bestehenden Werkstatt-APIs nötig, nur Lesen.
- **hr:** Falls Funktion (Werkstattleiter/Mechaniker/Azubi) aus employees oder eigenem Feld kommt.
- **controlling:** Später ggf. Kostenstelle/Reporting; nicht für MVP nötig.

---

## 5. Nächster Schritt

**Empfehlung:** Phase 1 (Konzept & Datenabgleich) starten: Excel-Formeln und Einheiten mit Fachbereich festziehen, dann 1.3 (Testmonat aus Locosoft) als kleines Script ausführen und mit Excel abgleichen. Danach Phase 2 (Schema) und 3 (API) umsetzen.
