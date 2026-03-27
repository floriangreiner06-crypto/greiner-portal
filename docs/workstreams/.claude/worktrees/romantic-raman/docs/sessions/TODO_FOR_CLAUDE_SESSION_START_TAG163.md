# TODO FOR CLAUDE - SESSION START TAG 163

**Letzte Session:** TAG 162 (2026-01-02)
**Fokus:** Zielplanung KST + Mitarbeiter

---

## KONTEXT

TAG 150-162 (02.01.2026) hat massiv aufgebaut:
- Werkstatt-Modularisierung
- Budget-Planungsmodul
- Unternehmensplan (1%-Ziel) GlobalCube-kompatibel
- KST-Ziele API + Dashboard
- Umlage-Neutralisierung
- YTD-Tracking Fixes

---

## HAUPTAUFGABEN TAG 163+

### Prioritaet 1: Zielplanung erweitern

**A) KST-Ziele Editor UI**
- Matrix: Monate (Sep-Aug) x Bereiche (NW, GW, Teile, Werkstatt, Sonstige)
- Inline-Editing der Zielwerte
- Speichern via POST /api/kst-ziele/ziele
- Kopieren von Vorjahres-Zielen

**B) Mitarbeiter-Ziele (NEU)**
- Neue Tabelle `mitarbeiter_ziele`
- Individuelle Ziele pro Mitarbeiter/Monat
- Bereiche: Verkauf (Stueck, DB1), Werkstatt (Stunden, Auslastung)
- Verknuepfung mit employees-Tabelle

```sql
CREATE TABLE mitarbeiter_ziele (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    geschaeftsjahr TEXT NOT NULL,
    monat INTEGER NOT NULL,  -- 1-12 (GJ)

    -- Verkauf-Ziele
    stueck_ziel INTEGER,
    db1_ziel NUMERIC(15,2),

    -- Werkstatt-Ziele
    stunden_ziel NUMERIC(10,2),
    auslastung_ziel NUMERIC(5,2),

    UNIQUE(employee_id, geschaeftsjahr, monat)
);
```

**C) Mitarbeiter-Dashboard**
- IST vs SOLL pro Mitarbeiter
- Ranking/Leaderboard
- Trend-Anzeige

### Prioritaet 2: Taeglich E-Mail-Report

Script fuer automatischen Versand:
- KST-Status (Daumen hoch/runter)
- Top/Flop Mitarbeiter (optional)
- Link zum Dashboard

### Prioritaet 3: Sonstige-Ziel pruefen

Aktuell nur 12% Erreichung - analysieren:
- Welche Konten gehoeren zu "Sonstige"?
- Ist Ziel realistisch?

---

## OFFENE PUNKTE (niedrigere Prio)

| Aufgabe | Quelle |
|---------|--------|
| fahrzeug_api.py Blueprint | TAG160 |
| GW-Dashboard CSV-Export | TAG160 |
| TEK-Dashboard GlobalCube-Validierung | TAG158 |
| BWA v2 Validierung | TAG158 |
| teile_data.py SSOT | TAG158 |
| Locosoft SOAP Client | TAG158 |

---

## WICHTIGE DATEIEN

```
api/kst_ziele_api.py           - KST-Zielplanung API
api/unternehmensplan_data.py   - 1%-Ziel Daten (mit Umlage-Filter)
templates/controlling/kst_ziele.html - KST-Ziele Dashboard
docs/KONTENPLAN_CONTROLLING.md - Umlage-Dokumentation
docs/FIRMENSTRUKTUR.md         - Firmenstruktur
```

---

## DATENBANK-REFERENZ

### employees (DRIVE Portal)
```sql
SELECT id, employee_number, first_name, last_name, department, active
FROM employees WHERE active = true
```

### Verkaufs-Zuordnung (Locosoft)
```sql
-- Verkaeufer zu Fahrzeug
SELECT salesperson_number, vehicle_number, db1
FROM dealer_vehicles WHERE out_invoice_date IS NOT NULL
```

### Werkstatt-Zuordnung (Locosoft)
```sql
-- Mechaniker zu Stunden
SELECT employee_number, SUM(duration_minutes)/60.0 as stunden
FROM times GROUP BY employee_number
```

---

## SERVER-BEFEHLE

```bash
# API testen
curl -s http://localhost:5000/api/kst-ziele/health
curl -s 'http://localhost:5000/api/kst-ziele/dashboard?monat=5'

# Sync
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/

# Neustart
sudo systemctl restart greiner-portal
```

---

*Vorbereitet fuer TAG 163*
