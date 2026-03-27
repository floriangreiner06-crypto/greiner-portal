# SESSION WRAP-UP TAG 133
**Datum:** 2025-12-22
**Thema:** Lieferforecast mit DB1-Prognose + SOAP-Fix

---

## Erledigte Aufgaben

### 1. SOAP-Client Bug gefixt
**Datei:** `tools/locosoft_soap_client.py` (Zeile 441)

```python
# Vorher (falsch)
result = self.service.readWorkOrderDetails(number=order_number)

# Nachher (richtig)
result = self.service.readWorkOrderDetails(orderNumber=order_number)
```

### 2. Vorfakturierte Rechnungen recherchiert
- PostgreSQL: `has_open_positions=true AND has_closed_positions=true`
- SOAP: `status=INVOICED_OPEN`
- Feld `vehicles.readmission_date` = geplante Kundenlieferung

### 3. Lieferforecast Dashboard erstellt
**URL:** `http://drive.auto-greiner.de/verkauf/lieferforecast`

**Features:**
- Geplante Fahrzeugauslieferungen (vehicles.readmission_date)
- DB1-Prognose pro Fahrzeug und Tag
- Filter: Zeitraum, Standort (DEG/LAN)
- Status: Offen / Vorfakturiert / Fakturiert

**KPIs:**
- Fahrzeuge gesamt
- Umsatz Brutto
- Vorfakturiert / Fakturiert
- DB1 Prognose (€ + %)

**Spalten Fahrzeugtabelle:**
- Lieferung, Standort, Marke, Modell
- Kennzeichen, Status, Brutto, DB1, DB1%

---

## Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `templates/verkauf_lieferforecast.html` | Dashboard-Template |

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/verkauf_api.py` | +210 Zeilen: `/api/verkauf/lieferforecast` Endpoint |
| `routes/verkauf_routes.py` | Route `/verkauf/lieferforecast` |
| `tools/locosoft_soap_client.py` | Parameter `number` → `orderNumber` |

---

## Datenquellen Lieferforecast

| Daten | Quelle | Tabelle/Feld |
|-------|--------|--------------|
| Geplante Lieferung | PostgreSQL | `vehicles.readmission_date` |
| Standort | PostgreSQL | `vehicles.subsidiary` (1=LAN, 2=DEG) |
| Rechnungsbeträge | PostgreSQL | `invoices.total_gross` |
| Status | PostgreSQL | `orders.has_open_positions/has_closed_positions` |
| DB1, Marke, Modell | SQLite | `sales.deckungsbeitrag`, `make_number`, `model_description` |

---

## Git Commits (diese Session)

```
e1f8d1c fix(SOAP): readWorkOrderDetails Parameter korrigiert
7dbea9a docs(TAG133): Session Wrap-Up + TODO TAG134
3b41660 feat(TAG133): Lieferforecast mit DB1-Prognose
```

---

## Offene Punkte für nächste Session

### 1. TEK Report Produktion aktivieren
- `scripts/send_daily_tek.py`: TEST_MODE = False
- Cronjob einrichten (17:30 Mo-Fr)

### 2. Carloop-Sync testen (von TAG131)
- `/test/ersatzwagen` aufrufen → "Carloop Sync" klicken

### 3. Automatischen Carloop-Sync-Job einrichten
- `scheduler/job_definitions.py` erweitern

---

## Sync-Befehle

```bash
# Lieferforecast syncen
cp /mnt/greiner-portal-sync/api/verkauf_api.py /opt/greiner-portal/api/
cp /mnt/greiner-portal-sync/routes/verkauf_routes.py /opt/greiner-portal/routes/
cp /mnt/greiner-portal-sync/templates/verkauf_lieferforecast.html /opt/greiner-portal/templates/

sudo systemctl restart greiner-portal
```

---

## Test-URLs
- **Lieferforecast:** `http://drive.auto-greiner.de/verkauf/lieferforecast`
- TEK Dashboard: `http://drive.auto-greiner.de/controlling/tek`
- Ersatzwagen: `http://drive.auto-greiner.de/test/ersatzwagen`
