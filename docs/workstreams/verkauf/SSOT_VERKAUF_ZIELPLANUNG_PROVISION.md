# SSOT-Check: Verkauf, Verkäufer-Zielplanung, Provisionsabrechnung

**Stand:** 2026-02-19  
**Zweck:** Redundanzen und verschiedene Quellen zwischen Verkäufer-Zielplanung und Provisionsabrechnung vermeiden; klare SSOT-Regeln für Verkaufsthemen.

---

## 1. Übersicht Datenquellen

| Thema | Modul | Quelle (Rohdaten) | Zeitbezug | Verkäufer-ID |
|-------|--------|-------------------|------------|--------------|
| **Auftragseingang** (Stückzahl/Verträge) | VerkaufData, Auftragseingang-Report, Mail | Portal `sales` | **Vertragsdatum** (`out_sales_contract_date`) | `sales.salesman_number` |
| **Verkäufer-Zielplanung** (Stückzahl Historie, Verteilung) | verkaeufer_zielplanung_api | **Locosoft direkt** (`dealer_vehicles`, `employees_history`) | **Vertragsdatum** (`out_sales_contract_date`) | `out_salesman_number_1` |
| **Provisionsabrechnung** (Rohdaten pro Monat) | provision_service | Portal `sales` | **Rechnungsdatum** (`out_invoice_date`) | `sales.salesman_number` |
| **Ziele (Jahresziele NW/GW)** | Verkäufer-Zielplanung, Monatsziele, Auftragseingang-Zielerfüllung | Portal `verkaeufer_ziele` + `zielplanung_stand` | – | `mitarbeiter_nr` (= Locosoft VKB) |

**Verkäufer-Identifikation:** Einheitlich **Locosoft-Mitarbeiternummer** (VKB). In Portal: `sales.salesman_number` = Sync von `dealer_vehicles.out_salesman_number_1`. Keine Redundanz bei der ID.

---

## 2. Bewusst getrennt (keine Redundanz)

- **Vertragsdatum vs Rechnungsdatum:**  
  - Zielplanung & Auftragseingang = **Auftragseingang** (Vertrag).  
  - Provision = **Fakturierung** (Rechnung = Abrechnungsmonat).  
  Das ist fachlich gewollt, keine Doppelquelle.

- **Zielplanung-Ziele:**  
  Nur in `verkaeufer_ziele` / `zielplanung_stand`. Monatsziele und Auftragseingang-Zielerfüllung lesen daraus (nur bei Status „freigegeben“). Die Provisionsabrechnung nutzt **keine** Ziele; wenn später „Zielerfüllung“ in der Provision angezeigt wird, muss ausschließlich diese Quelle genutzt werden (z. B. Monatsziele-API).

- **Provisionslogik:**  
  SSOT ist `api/provision_service.py` (Konfiguration `provision_config`, Rohdaten `get_sales_for_provision` aus `sales`). Keine parallele Berechnung in Zielplanung.

---

## 3. Potenzielle Redundanzen / Abweichungen

### 3.1 Auftragseingang-Stückzahl: zwei Implementierungen

| Aspekt | VerkaufData (sales) | Verkäufer-Zielplanung (Locosoft) |
|--------|----------------------|-----------------------------------|
| **Quelle** | Portal `sales` (Sync von Locosoft) | Locosoft `dealer_vehicles` direkt |
| **Dedup** | Ja (N nicht zählen wenn T/V gleiche VIN+Datum) | Ja (gleiche Logik in SQL) |
| **Verkäufer-Name** | Portal `employees` (sync von Locosoft), `e.locosoft_id` | Locosoft `employees_history` |

**Risiko:**  
- Sync-Verzögerung: Zielplanung sieht ggf. neuere Locosoft-Daten als VerkaufData (wenn Sync noch nicht gelaufen).  
- Verkäufer-Namen: zwei Quellen (`employees` vs `employees_history`) können abweichen (Schreibweise, Aktualität).

**Empfehlung:**  
- **Langfristig:** Eine SSOT für „Auftragseingang Stückzahl pro Verkäufer (Jahr/Monat, NW/GW)“ definieren. Entweder: (a) VerkaufData um eine Methode „Stückzahl pro Verkäufer pro Jahr (Vertragsdatum, NW/GW, ggf. nach Marke)“ erweitern und Zielplanung ruft diese statt Locosoft auf; oder (b) explizit dokumentieren, dass Zielplanung aus Performance/Historie Locosoft direkt nutzt und VerkaufData für Tages-/Monats-Auftragseingang – dann gleiche Definitionen (Dedup, NW/GW) sicherstellen (siehe 3.2).  
- **Verkäufer-Namen:** Eine Quelle festlegen (z. B. Portal `employees` als SSOT nach Sync); Zielplanung könnte Namen optional aus Portal nachladen, wo verfügbar.

### 3.2 Definition NW vs GW (T = Tageszulassung) – **umgesetzt inkl. T-Regel**

**Verkaufsleitung:** T (Tageszulassung) = NW **nur bis 1 Jahr ab Erstzulassung**; älter als 1 Jahr = GW.

| Definition | Typen |
|------------|--------|
| **NW** (Neuwagen) | N, V; **T** nur wenn (Vertragsdatum − Erstzulassung) ≤ 365 Tage (oder Ez fehlt) |
| **GW** (Gebrauchtwagen) | D, G; **T** wenn (Vertragsdatum − Erstzulassung) > 365 Tage |

- **Erstzulassung:** Portal `sales.first_registration_date` (Sync aus Locosoft `vehicles`); Zielplanung: Locosoft `vehicles.first_registration_date` (JOIN).
- **VerkaufData:** `_NW_GW_CASE_ART`, `_NW_SUM_CASE`, `_GW_SUM_CASE` in get_auftragseingang, get_verkaufer_performance.
- **Verkäufer-Zielplanung:** Gleiche T-Regel in _stueckzahl_fuer_jahr und _saisonalitaet_fuer_jahr (JOIN auf vehicles).

### 3.3 Kategorien Neuwagen/Testwagen/Gebraucht

- **Provisionsabrechnung** nutzt `out_sale_type` (F/N/D/L/T/V/B/G) und mappt auf Kategorien I (Neuwagen), II (Testwagen/VFW), III (Gebrauchtwagen) – siehe `provision_service.TYP_TO_KAT`.  
- **Zielplanung** nutzt nur NW/GW (N,V,T vs D,G) ohne Testwagen als eigene Kategorie.

Keine Überschneidung: Provision braucht Feinaufteilung (DB vs Rg.Netto, Min/Max), Zielplanung nur NW/GW. Keine Redundanz, solange keine „Zielerfüllung“ in der Provision mit Zielplanungs-Zielen vermischt wird – dann ausschließlich `verkaeufer_ziele`/Monatsziele-API nutzen.

---

## 4. Konkrete SSOT-Regeln (für beide Module)

1. **Verkäufer-ID:** Überall **Locosoft-Mitarbeiternummer** (VKB). In Portal: `sales.salesman_number`, in `verkaeufer_ziele`: `mitarbeiter_nr`, in Provision: `verkaufer_id` / VKB. Keine eigenen IDs erfinden.

2. **Verkaufs-Rohdaten (Fakturierung):** Einzige Quelle für Provision und für Auslieferungen/Fakturierung = Portal **`sales`** (gefüllt durch Sync aus Locosoft). Provision filtert nach `out_invoice_date`; andere Module nach Bedarf nach `out_sales_contract_date` oder `out_invoice_date`.

3. **Auftragseingang (Vertragsdatum):** Heute zwei Quellen (sales vs Locosoft). Siehe 3.1 – entweder auf eine SSOT (VerkaufData) vereinheitlichen oder Abgrenzung + gleiche NW/GW/Dedup-Definition dokumentieren und einhalten.

4. **Jahresziele / Monatsziele:** Einzige Quelle = **`verkaeufer_ziele`** + **`zielplanung_stand`**. Nutzung nur bei Status „freigegeben“. Keine Kopie der Ziele in Provision-Tabellen; bei Zielerfüllung in der Provision nur lesend die bestehende API (z. B. Monatsziele) nutzen.

5. **Provisionsberechnung:** Einzige Logik = **`api/provision_service.py`** (Konfiguration aus `provision_config`). Keine doppelte Formel in Zielplanung oder Scripts.

6. **Verkäufer-Stammdaten (Name, Zuordnung User):** Heute Portal `employees` (u. a. für Auftragseingang, Provision-VKB-Zuordnung) und Locosoft `employees_history` (Zielplanung). Empfohlen: **Portal `employees`** als SSOT nach Sync; Zielplanung kann Namen von dort beziehen, sobald technisch sinnvoll (Performance/Verfügbarkeit).

---

## 5. Nächste Schritte (optional)

- [x] NW/GW-Definition (T = Tageszulassung = NW) einheitlich: SSOT in `api/verkauf_data.FAHRZEUGTYP_NW` / `FAHRZEUGTYP_GW`; VerkaufData und Verkäufer-Zielplanung nutzen diese Konstanten.
- [ ] VerkaufData um „Stückzahl pro Verkäufer pro Jahr (Vertrag, NW/GW)“ erweitern und Zielplanung darauf umstellen ODER Abgrenzung „sales = Tages/Monats-Auftragseingang, Locosoft = Jahres-Stückzahl Zielplanung“ in CONTEXT.md festhalten.
- [ ] Verkäufer-Namen: Zielplanung optional aus Portal `employees` beziehen (oder Sync employees_history → Portal dokumentieren).
- [ ] Wenn Provision „Zielerfüllung“ anzeigt: nur Monatsziele-API / verkaeufer_ziele (freigegeben) nutzen, keine eigene Ziele-Logik.

---

## 6. Kurzreferenz

| Was | SSOT / Quelle |
|-----|----------------|
| Verkäufer-ID | Locosoft-Mitarbeiternummer (sales.salesman_number, verkaeufer_ziele.mitarbeiter_nr) |
| Verkäufe (Fakturierung) | Portal `sales`, Filter `out_invoice_date` |
| Auftragseingang (Vertrag) | Portal `sales` (VerkaufData) ODER Locosoft (Zielplanung) – siehe 3.1 |
| Jahresziele NW/GW | `verkaeufer_ziele` + `zielplanung_stand` (nur freigegeben) |
| Monatsziele / Zielerfüllung | API verkaeufer_zielplanung (monatsziele, planungsstand) |
| **NW/GW (Auftragseingang, Zielplanung)** | **`api/verkauf_data.FAHRZEUGTYP_NW` / `FAHRZEUGTYP_GW`** (T = Tageszulassung = NW) |
| Provisionsberechnung | `api/provision_service.py` + `provision_config` |
| Provisions-Rohdaten | `get_sales_for_provision()` → `sales` nach `out_invoice_date` |
