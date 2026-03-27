# TODO FOR CLAUDE - SESSION START TAG139

**Erstellt:** 2025-12-25

---

## Offene Aufgaben

### 1. TEK v2 Stückzahlen testen
- VIN-basierte Zählung wurde implementiert (TAG138)
- Prüfen ob Zahlen im Drill-Down plausibel sind
- Browser mit Strg+F5 refreshen

### 2. Buchhaltung klären: "Privat a reg"
- Absatzweg hat nur Einsatz-Konten (724201, 724202)
- Kein separates Erlös-Konto vorhanden
- Frage: Wo wird der Erlös gebucht? (vermutlich 824200 "Privat reg")

---

## Technischer Stand

### TEK v2 Stückzahlen
```sql
-- Alt (zählte Buchungszeilen):
COUNT(DISTINCT j.vehicle_reference) as stueck

-- Neu (zählt echte Fahrzeuge via VIN):
COUNT(DISTINCT SUBSTRING(j.vehicle_reference FROM 'FG:([A-Z0-9]+)')) as stueck
```

### Datenbank
- **PostgreSQL** (10.80.80.8) - Alle Daten
- SQLite wird NICHT mehr verwendet

---

## Wichtige Dateien

| Modul | Dateien |
|-------|---------|
| TEK v2 | `templates/controlling/tek_dashboard_v2.html`, `routes/controlling_routes.py` |

---

## Hinweise für nächste Session

1. Server läuft mit neuer Version
2. PostgreSQL für alle Abfragen nutzen
3. VIN-Verknüpfung: `journal_accountings.vehicle_reference` enthält `FG:<VIN>`
