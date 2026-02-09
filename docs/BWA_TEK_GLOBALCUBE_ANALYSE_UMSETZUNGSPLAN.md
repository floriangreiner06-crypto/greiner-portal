# BWA / TEK / Globalcube – Analyse und Umsetzungsplan

**Datum:** 2026-02-09  
**Anlass:** Landau fehlt im TEK-Dashboard (Metabase); Konsistenz und Vermeidung von Redundanz

---

## 1. Kurzfassung

- **Ursache „Landau fehlt“:** Die Metabase-Query **„TEK nach Standort“** filtert fälschlich mit `standort_id IN (1, 2)` und mappt nur 1 und 2 auf Namen. Standort **3 (Landau)** ist in `fact_bwa` und `dim_standort` korrekt abgebildet, wurde aber in der Query ausgelassen.
- **SSOT:** Standort-Logik ist in `api/standort_utils.py` und `docs/STANDORT_LOGIK_SSOT.md` zentral definiert. `fact_bwa` nutzt `subsidiary_to_company_ref` als `standort_id` (1=DEG, 2=HYU, 3=LAN).
- **Empfehlung:** Query anpassen (Landau einbeziehen), alle Auswertungen an dieselbe SSOT anbinden, Doppellogik vermeiden.

---

## 2. Bestehende Dokumentation und SSOT

### 2.1 Standort-Mapping (SSOT)

| Quelle | Inhalt |
|--------|--------|
| **`api/standort_utils.py`** | `STANDORT_NAMEN`, `BETRIEB_NAMEN`, `STANDORT_KUERZEL`, `STANDORTE`; Filter: `build_bwa_filter`, `build_locosoft_filter_*` |
| **`docs/STANDORT_LOGIK_SSOT.md`** | Autoritative Doku: ID 1=Deggendorf Opel, 2=Deggendorf Hyundai, 3=Landau; BWA/Locosoft-Filter-Logik |
| **Migration `create_finanzreporting_cube_tag178.sql`** | `dim_standort`: `standort_id` = `subsidiary_to_company_ref`, 1=DEG, 2=HYU, 3=LAN; `fact_bwa.standort_id` = dieselbe Quelle |

**Wichtig:** Für BWA/TEK in `loco_journal_accountings` bzw. `fact_bwa` gilt:
- **Umsatz:** Standort über `branch_number` (1=DEG, 2=HYU, 3=Landau).
- **fact_bwa:** Verwendet `subsidiary_to_company_ref` als `standort_id` (1/2/3). Damit sind alle drei Standorte in den Daten vorhanden, sofern Buchungen existieren.

### 2.2 BWA / TEK / Globalcube – bereits vorhandene Doku

| Thema | Dokumente / Orte |
|-------|-------------------|
| **BWA Landau Filter** | `docs/BWA_LANDAU_FILTER_KORREKTUR_FINAL_TAG182.md`, `BWA_LANDAU_HAR_ANALYSE_TAG182.md` – Umsatz/Einsatz Landau (branch_number=3, 6. Ziffer) |
| **Globalcube Reverse Engineering** | `docs/GLOBALCUBE_BWA_MAPPING_EXPLORATION_TAG182.md`, `docs/globalcube_analysis/` (Konten, Struktur, Abweichungen) |
| **Konten / KST** | `docs/KONTENMAPPING_KST_LOGIK_KORREKTUR_TAG181.md` – 2. Ziffer = KST, 6. Ziffer = Filiale (1=DEG, 2=Landau) |
| **Metabase & Views** | `docs/METABASE_ARCHITEKTUR_ANALYSE.md`, `METABASE_VIEWS_UMSTELLUNG.md`, `METABASE_VORZEICHEN_KORREKTUR.md` |
| **Firmenstruktur** | `docs/ANALYSE_FIRMENSTRUKTUR_ST_ANTEIL_BERECHNUNG.md` – subsidiary 1=DEGO, 2=DEGH, 3=LANO |

Es gibt also bereits eine klare Trennung: SSOT für Standorte, BWA-Filter (inkl. Landau), Konten/KST, Globalcube-Mapping und Metabase/Views. **Nicht nötig:** Logik neu zu erfinden; **nötig:** alle Abfragen (DRIVE, Metabase, Scripts) auf diese Quellen ausrichten.

---

## 3. Warum Landau im TEK-Dashboard fehlt

- **Datenbasis:** `fact_bwa` und `dim_standort` kennen standort_id **1, 2, 3** (Migration + Datenquelle `subsidiary_to_company_ref`).
- **Fehler:** In `scripts/update_metabase_queries_to_views.py` ist die Query **„TEK nach Standort“** (ID 43) so definiert:
  - `AND standort_id IN (1, 2)` in beiden CTEs (`umsatz_data`, `einsatz_data`) → **Landau (3) wird ausgeschlossen.**
  - CASE für die Anzeige: nur `1 → Deggendorf Opel`, `2 → Hyundai`, `ELSE → Sonstige` → **kein Eintrag für 3 = Landau.**

Damit ist die Inkonsistenz ausschließlich in dieser einen Metabase-Query (bzw. im Script, das sie befüllt), nicht in der Datenmodellierung oder in `dim_standort`/`fact_bwa`.

---

## 4. Redundanzen und Doppelarbeit vermeiden

### 4.1 Bereits zentralisiert (nutzen, nicht duplizieren)

- **Standort-Namen und -Filter:** `api/standort_utils.py` + `STANDORT_LOGIK_SSOT.md`.
- **BWA-Filter-Logik (DRIVE):** `api/controlling_api.py::build_firma_standort_filter()`, Aufruf ggf. über `standort_utils.build_bwa_filter()`.
- **Finanzreporting-Cube:** `fact_bwa`, `dim_standort`, `dim_zeit`, `dim_kostenstelle`, `dim_konto` in `migrations/create_finanzreporting_cube_tag178.sql`; Refresh über `refresh_finanzreporting_cube()` und Celery.

### 4.2 Wo noch angeglichen werden sollte

- **Metabase „TEK nach Standort“:** Standortliste und -namen aus der SSOT ableiten: alle drei Standorte (1, 2, 3) einbeziehen und Namen konsistent mit `STANDORT_NAMEN` (z. B. „Landau“ bzw. „Landau Opel“).
- **G&V-Filter:** DRIVE nutzt `NOT (subsidiary_to_company_ref = 0 AND document_number::text LIKE 'GV%')`; `fact_bwa` nutzt `posting_text NOT LIKE '%G&V-Abschluss%'`. Optional langfristig in der Migration vereinheitlichen (siehe `METABASE_VORZEICHEN_KORREKTUR.md`).
- **Weitere Metabase-Queries:** Prüfen, ob irgendwo noch fest „nur Standort 1,2“ oder eigene Standort-Mappings stehen; wenn ja, auf (1,2,3) und SSOT umstellen.

### 4.3 Keine neue „Parallel-Entwicklung“

- Keine neuen Standort-Tabellen oder -Mappings außerhalb von `standort_utils` und `dim_standort`.
- Keine neuen „eigenen“ BWA/TEK-Kontenlogiken in Metabase; Kontenbereiche und Bereichslogik aus bestehender Doku/Kode nutzen (z. B. 81/82/83/84/86 für Umsatz, 71–76 für Einsatz, siehe Kontenmapping/KST-Doku).

---

## 5. Umsetzungsplan

### Phase 1 – Sofort (Landau im TEK-Dashboard) ✅ umgesetzt (TAG 216)

1. **`scripts/update_metabase_queries_to_views.py` angepasst**
   - Query **„TEK nach Standort“** (ID 43): `standort_id IN (1, 2, 3)`; CASE um **`WHEN 3 THEN 'Landau'`** ergänzt; „Deggendorf Hyundai“ statt „Hyundai“.

2. **Ursache behoben: Standort in den Views**
   - **Problem:** `fact_bwa` und `dim_standort` nutzten `subsidiary_to_company_ref` als standort_id → nur 2 Werte (1=Stellantis, 2=Hyundai); Landau (branch_number=3) wurde mit Deggendorf Opel zu 1 zusammengefasst.
   - **Lösung:** Migration **`fix_finanzreporting_standort_branch_number_tag216.sql`**: `standort_id = branch_number` (1=DEG, 2=HYU, 3=Landau) gemäß SSOT.
   - **Ergebnis:** `dim_standort` hat 3 Zeilen; `fact_bwa` enthält standort_id 1, 2, 3 (Landau ~97k Buchungen).

3. **Metabase-Query aktualisiert**
   - `update_metabase_queries_to_views.py` ausgeführt → alle TEK/BWA-Queries in Metabase aktualisiert.
   - TEK-Dashboard nach F5: Landau erscheint in „TEK nach Standort“, sofern Daten für den Monat vorhanden.

### Phase 2 – Kurzfristig (Konsistenz)

3. **Dokumentation**
   - In `docs/METABASE_VIEWS_UMSTELLUNG.md` ggf. korrigieren: „dim_standort: 2 Zeilen“ → Hinweis, dass bei vorhandenen Buchungen für alle drei Standorte drei Zeilen (1=DEG, 2=HYU, 3=LAN) vorkommen; Landau darf in keiner Query ausgeschlossen werden.

4. **Einmalige Prüfung**
   - Alle Metabase-Queries (TEK + BWA) nach fest codierten Standort-Listen durchsuchen; wo nötig auf (1, 2, 3) und einheitliche Namen (aus SSOT) umstellen.

### Phase 3 – Optional / Langfristig

5. **G&V-Filter**
   - In `create_finanzreporting_cube_tag178.sql` prüfen, ob der G&V-Ausschluss in `fact_bwa` an die DRIVE-Logik (`subsidiary_to_company_ref = 0 AND document_number LIKE 'GV%'`) angeglichen werden soll, um Abweichungen (z. B. bei Neuwagen-Umsatz) zu minimieren.

6. **DRIVE API auf Views**
   - Wie in `METABASE_ARCHITEKTUR_ANALYSE.md` beschrieben: optional Teile der DRIVE-BWA/TEK-API auf `fact_bwa`/dim_* umstellen, um eine einzige Datenquelle für DRIVE und Metabase zu haben.

---

## 6. Referenzen (ohne Doppelarbeit)

- **Standort SSOT:** `api/standort_utils.py`, `docs/STANDORT_LOGIK_SSOT.md`
- **BWA/TEK Filter (DRIVE):** `api/controlling_api.py`, `routes/controlling_routes.py`
- **Landau BWA:** `docs/BWA_LANDAU_FILTER_KORREKTUR_FINAL_TAG182.md`
- **Konten/KST:** `docs/KONTENMAPPING_KST_LOGIK_KORREKTUR_TAG181.md`
- **Globalcube:** `docs/GLOBALCUBE_BWA_MAPPING_EXPLORATION_TAG182.md`, `docs/globalcube_analysis/`
- **Metabase/Views:** `docs/METABASE_ARCHITEKTUR_ANALYSE.md`, `docs/METABASE_VIEWS_UMSTELLUNG.md`, `docs/METABASE_VORZEICHEN_KORREKTUR.md`
- **Migration/Refresh:** `migrations/create_finanzreporting_cube_tag178.sql`, `celery_app/tasks.py` (`refresh_finanzreporting_cube`)

---

**Fazit:** Landau fehlt nur wegen einer zu engen Filterung in der Metabase-Query. Mit der Anpassung auf `standort_id IN (1, 2, 3)` und der Ergänzung der Anzeige für Standort 3 ist das Problem behoben. Durch Nutzung der bestehenden SSOT und Doku vermeiden wir Redundanz und Doppelarbeit bei BWA/TEK und Globalcube.
