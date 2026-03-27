# TODO FOR CLAUDE - SESSION START TAG140

**Erstellt:** 2025-12-28

---

## Erledigte Aufgaben (TAG139)

- PostgreSQL Migration komplett funktionsfahig
- HybridRow/HybridCursor fur gemischte Zugriffsmuster
- Alle SQLite-Syntax (strftime, date('now'), julianday) konvertiert
- vacation_api, bankenspiegel_api, mail_api, organization_api, teile_status_api, verkauf_api gefixt

---

## Offene Aufgaben

### 1. TEK v2 Stuckzahlen testen
- VIN-basierte Zahlung wurde implementiert (TAG138)
- Prufen ob Zahlen im Drill-Down plausibel sind
- Browser mit Strg+F5 refreshen

### 2. Buchhaltung klaren: "Privat a reg"
- Absatzweg hat nur Einsatz-Konten (724201, 724202)
- Kein separates Erlos-Konto vorhanden
- Frage: Wo wird der Erlos gebucht? (vermutlich 824200 "Privat reg")

### 3. Optional: Datumsformat-Normalisierung
- `all-bookings` API gibt gemischte Datumsformate zuruck
- ISO (2025-01-01) vs RFC (Thu, 02 Jan 2025...)
- Sortierung funktioniert uber str(), aber Format sollte vereinheitlicht werden

---

## Technischer Stand

### Datenbanken
- **PostgreSQL** (10.80.80.8) - Locosoft (extern)
- **PostgreSQL** (127.0.0.1) - Drive Portal (drive_portal)
- SQLite wird NICHT mehr verwendet

### HybridRow (TAG 139)
```python
# Beide Zugriffsmuster funktionieren:
row[0]      # Index-Zugriff
row['name'] # Dict-Zugriff
```

---

## Wichtige Dateien

| Modul | Dateien |
|-------|---------|
| DB Connection | `api/db_connection.py` (HybridRow, HybridCursor) |
| DB Utils | `api/db_utils.py` (row_to_dict angepasst) |
| TEK v2 | `templates/controlling/tek_dashboard_v2.html`, `routes/controlling_routes.py` |
| Vacation | `api/vacation_api.py`, `api/vacation_chef_api.py` |

---

## Hinweise fur nachste Session

1. Server lauft mit neuer Version
2. PostgreSQL fur ALLE Abfragen
3. HybridRow fur gemischte Code-Pattern
