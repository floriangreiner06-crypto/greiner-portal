# DB-Problem: Tabelle "times" existiert nicht

**Datum:** TAG 194  
**Problem:** Spinner auf `/werkstatt/stempeluhr`, `/werkstatt/cockpit`, `/werkstatt/stempeluhr/monitor`

## Problem

Die Tabelle `times` existiert nicht in der Locosoft PostgreSQL-DB (`loco_auswertung_db`).

**Verfügbare Tabellen:**
- ✅ `labours` (existiert)
- ✅ `orders` (existiert)
- ❌ `times` (existiert NICHT)
- ❌ `loco_times` (existiert NICHT in dieser DB)

**Code verwendet:**
- `FROM times` (77 Stellen in `werkstatt_data.py`)
- `FROM orders` 
- `FROM labours`

## Mögliche Lösungen

1. **Views erstellen:** Views `times`, `orders`, `labours` die auf die echten Tabellen zeigen
2. **Tabellennamen ändern:** Alle Queries von `times` zu `loco_times` ändern
3. **Schema prüfen:** Vielleicht gibt es ein anderes Schema mit diesen Tabellen

## Betroffene Endpoints

- `/werkstatt/stempeluhr` → `get_stempeluhr()` → verwendet `times`
- `/werkstatt/cockpit` → verwendet `get_stempeluhr()` → verwendet `times`
- `/werkstatt/stempeluhr/monitor` → verwendet `get_stempeluhr()` → verwendet `times`

## Status Leerlaufaufträge

✅ **Bereits implementiert:** `get_stempeluhr()` verwendet `LEERLAUF_AUFTRAEGE_PRO_BETRIEB`:
- DEGO: 39406
- DEGH: 220710
- LANO: 313666

## Nächste Schritte

1. Prüfen ob Views existieren oder erstellt werden müssen
2. Oder Tabellennamen in allen Queries anpassen
3. Service neustarten nach Fix
