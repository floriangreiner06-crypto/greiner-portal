# TODO FOR CLAUDE - SESSION START TAG 164

**Letzte Session:** TAG 163 (2026-01-02)
**Fokus:** Serviceberater-Ziele + 5-Fragen-Wizard erweitern

---

## KONTEXT

TAG 148-163 (02.01.2026) hat massiv aufgebaut:
- Werkstatt-Modularisierung (-54% LOC)
- Budget-Planungsmodul mit 5-Fragen-Wizard
- Unternehmensplan GlobalCube-kompatibel
- KST-Ziele API + Dashboard
- Umlage-Neutralisierung

Konsolidierte TODO-Liste: `docs/sessions/KONSOLIDIERTE_TODOS_TAG163.md`

---

## HAUPTAUFGABEN TAG 164+

### Prioritaet 1A: Serviceberater-Ziele (ERSTES ZIEL)

**Tabelle erstellen:**
```sql
CREATE TABLE mitarbeiter_ziele (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    geschaeftsjahr TEXT NOT NULL,
    monat INTEGER NOT NULL,
    -- Serviceberater-Ziele
    stunden_ziel NUMERIC(10,2),
    auslastung_ziel NUMERIC(5,2),
    umsatz_ziel NUMERIC(15,2),
    -- Spaeter: Verkauf
    stueck_ziel INTEGER,
    db1_ziel NUMERIC(15,2),
    kommentar TEXT,
    erstellt_von VARCHAR(100),
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, geschaeftsjahr, monat)
);
```

**API erstellen:** `api/mitarbeiter_ziele_api.py`
- GET /api/mitarbeiter-ziele/health
- GET /api/mitarbeiter-ziele/serviceberater - Alle Serviceberater mit IST/SOLL
- GET /api/mitarbeiter-ziele/dashboard - Uebersicht
- POST /api/mitarbeiter-ziele/ziele - Ziele speichern

**Dashboard:** IST vs SOLL, Ranking, Trend

### Prioritaet 1B: 5-Fragen-Wizard fuer 1%-Ziel erweitern

Aktueller Wizard: `templates/verkauf_budget_wizard.html`
- Nur NW und GW
- Stueck, Umsatz, DB1

**Erweitern auf:**
- Alle KST: NW, GW, Teile, Werkstatt, Sonstige
- 1%-Renditeziel als Ausgangspunkt
- Gap-Berechnung: Was fehlt zum Ziel?
- Verteilung auf Bereiche vorschlagen

### Prioritaet 1D: Potenziale erfassen

**Offene Auftraege als Potenzial:**
- Daten aus werkstatt_data.py: `get_offene_auftraege()`
- Wert der offenen Auftraege berechnen
- Als Potenzial im Dashboard anzeigen

**Weitere Potenziale:** User-Input abwarten

---

## WICHTIGE DATEIEN

```
# Bestehend (nutzen!)
api/kst_ziele_api.py           - KST-Zielplanung API
api/werkstatt_data.py          - Mechaniker/Serviceberater-Daten
api/budget_api.py              - Budget-Wizard API
templates/verkauf_budget_wizard.html - 5-Fragen-Wizard

# Neu erstellen
api/mitarbeiter_ziele_api.py   - Serviceberater-Ziele
templates/controlling/mitarbeiter_ziele.html - Dashboard
```

---

## DATENBANK-REFERENZ

### Serviceberater in employees
```sql
SELECT id, employee_number, first_name, last_name, department, position
FROM employees
WHERE active = true
  AND (department ILIKE '%service%' OR position ILIKE '%serviceberater%')
```

### Serviceberater-IST aus Locosoft
```sql
-- Umsatz pro Serviceberater
SELECT
    employee_number,
    SUM(invoice_total) as umsatz
FROM orders
WHERE invoice_date >= '2025-09-01'
GROUP BY employee_number
```

---

## SERVER-BEFEHLE

```bash
# Tabelle erstellen
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "
CREATE TABLE mitarbeiter_ziele (...)
"

# API testen
curl -s http://localhost:5000/api/mitarbeiter-ziele/health

# Sync
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/

# Neustart
sudo systemctl restart greiner-portal
```

---

## FIRMENSTRUKTUR (WICHTIG!)

```
AUTOHAUS GREINER GmbH & Co. KG (Stellantis = Opel + Leapmotor)
- Standorte: Deggendorf + Landau
- HAT das Personal (alle Mitarbeiter!)
- subsidiary_to_company_ref = 1

AUTO GREINER GmbH & Co. KG (Hyundai)
- Standort: Deggendorf
- HAT KEIN eigenes Personal
- subsidiary_to_company_ref = 2
```

---

*Vorbereitet fuer TAG 164*
