# DB-Problem Analyse: Tabelle "times" existiert nicht

**Datum:** TAG 194  
**Problem:** Spinner auf `/werkstatt/stempeluhr`, `/werkstatt/cockpit`, `/werkstatt/stempeluhr/monitor`

## Analyse

### Status

1. ✅ **Neue Leerlaufaufträge:** `get_stempeluhr()` verwendet bereits `LEERLAUF_AUFTRAEGE_PRO_BETRIEB`
2. ❌ **DB-Problem:** Tabelle `times` existiert nicht in Locosoft-DB
3. ⚠️ **Dokumentation vs. Realität:** Dokumentation erwähnt `times (VIEW)`, aber View existiert nicht

### Verfügbare Tabellen in Locosoft-DB (`loco_auswertung_db`)

- ✅ `orders` (BASE TABLE)
- ✅ `labours` (BASE TABLE)
- ❌ `times` (existiert NICHT)
- ❌ `loco_times` (existiert NICHT in dieser DB)

### Code verwendet

- `FROM times` (77 Stellen in `werkstatt_data.py`)
- `FROM orders` ✅
- `FROM labours` ✅

## Wann hat sich der Namensbezug geändert?

**Git-Historie zeigt:**
- Keine Migration von `loco_times` zu `times`
- Code verwendet schon immer `times`
- Dokumentation erwähnt `times (VIEW)`, aber View wurde nie erstellt

**Mögliche Ursachen:**
1. Views wurden nie erstellt (Setup-Script fehlt)
2. Views wurden gelöscht (unbeabsichtigt)
3. Tabellennamen in Locosoft-DB sind anders als erwartet

## Lösung

### Option 1: Views erstellen (EMPFOHLEN)

```sql
-- In Locosoft-DB (loco_auswertung_db) ausführen:
CREATE VIEW times AS SELECT * FROM <echte_tabelle>;
CREATE VIEW orders AS SELECT * FROM <echte_tabelle>;  -- Falls nötig
CREATE VIEW labours AS SELECT * FROM <echte_tabelle>;  -- Falls nötig
```

**Problem:** Wir wissen nicht, welche Tabelle `times` ersetzen soll!

### Option 2: Tabellennamen im Code ändern

- Alle `FROM times` → `FROM <echte_tabelle>`
- 77 Stellen in `werkstatt_data.py` ändern

**Problem:** Wir wissen nicht, wie die echte Tabelle heißt!

## Nächste Schritte

1. **Prüfen:** Welche Tabelle enthält die Stempelzeiten in der Locosoft-DB?
2. **Views erstellen:** Oder Tabellennamen im Code anpassen
3. **Service neustarten:** Nach Fix

## Betroffene Endpoints

- `/werkstatt/stempeluhr` → `get_stempeluhr()` → verwendet `times`
- `/werkstatt/cockpit` → verwendet `get_stempeluhr()` → verwendet `times`
- `/werkstatt/stempeluhr/monitor` → verwendet `get_stempeluhr()` → verwendet `times`

## Redundanzen / Code-Fehler

**Keine Redundanzen gefunden:**
- Leerlaufaufträge sind zentralisiert in `LEERLAUF_AUFTRAEGE_PRO_BETRIEB`
- `build_leerlauf_filter()` ist SSOT für Filter-Logik

**Code-Fehler:**
- ❌ Tabelle `times` existiert nicht → alle Queries schlagen fehl
- ⚠️ Dokumentation ist veraltet (erwähnt `times (VIEW)`, aber View existiert nicht)
