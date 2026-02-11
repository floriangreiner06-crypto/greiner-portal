# TAG 93 - Session Wrap-Up
**Datum:** 2025-12-05
**Dauer:** ~2 Stunden

---

## Erledigte Aufgaben

### 1. Nachkalkulation - Verlustberechnung korrigiert
**Problem:** Verlust wurde aus Rechnungspreis / Vorgabe-AW berechnet (ungenau)

**Lösung:** Verrechnungssätze aus `charge_types.timeunit_rate` verwenden

| Typ | Beschreibung | €/AW |
|-----|--------------|------|
| 10 | Lohn Mechanik | 11,90€ |
| 11 | Lohn Wartung | 11,90€ |
| 15 | Lohn Elektrik | 12,90€ |
| 16 | Elektrofahrzeuge | 17,90€ |
| 20 | Lohn Karosserie | 21,00€ |
| 60 | Lohn Garantie | 8,43€ |

### 2. Invoice-Type Filter
**Problem:** Fahrzeugverkäufe (Typ 7, 8) erschienen in Nachkalkulation mit 16.000€+ Rechnungen

**Lösung:** Filter auf `invoice_type IN (2, 4, 5, 6)` - nur echte Werkstattarbeit

### 3. Intern/Extern Filter
**Neuer Parameter:** `?typ=alle|extern|intern`

**Intern-Erkennung:**
- Kundennummer = 3000001
- Name enthält "intern" oder "greiner" + "auto"

**Ergebnis heute:**
- 32 externe Aufträge (LG: 78%)
- 5 interne Aufträge (LG: 87,6%)

### 4. Auftrag-Modal statt neuem Tab
**Vorher:** Klick auf Auftragsnummer → neuer Tab mit Stempeluhr
**Nachher:** Popup-Modal mit Auftragsdetails (Fahrzeug, Kunde, Positionen, Teile)

---

## Geänderte Dateien
```
api/werkstatt_live_api.py
  - labour_summen CTE: JOIN auf charge_types für aw_preis_db
  - SELECT: aw_preis_db hinzugefügt
  - Verlustberechnung: aw_preis_db statt rechnung/vorgabe
  - LIKE-Escape: %% für psycopg2

templates/aftersales/werkstatt_tagesbericht.html
  - showAuftrag(): Modal statt window.open
  - renderAuftragModal(): Auftragsdetails darstellen
  - Modal-HTML hinzugefügt
```

---

## API Endpoints

### Nachkalkulation
```
GET /api/werkstatt/live/nachkalkulation
  ?datum=2025-12-05
  &subsidiary=1
  &typ=extern|intern|alle
```

### Auftrag-Details
```
GET /api/werkstatt/live/auftrag/38898
```

---

## Git
```
Commit: b2fd6b4
Branch: feature/tag82-onwards
Message: TAG93: Nachkalkulation mit DB-Verrechnungssätzen + Auftrag-Modal
```

---

## Nächste Schritte (optional)
- [ ] Filter-Buttons im UI für Intern/Extern
- [ ] Stempelungen im Auftrag-Modal anzeigen
- [ ] MA 1 (Dummy) aus allen Auswertungen filtern
