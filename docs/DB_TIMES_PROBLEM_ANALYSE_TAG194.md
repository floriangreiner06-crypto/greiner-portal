# DB-Problem: Tabelle "times" existiert nicht - Vollständige Analyse

**Datum:** TAG 194  
**Problem:** Spinner auf `/werkstatt/stempeluhr`, `/werkstatt/cockpit`, `/werkstatt/stempeluhr/monitor`

## 🔍 Vollständige Analyse

### Aktuelle Situation

1. **Code verwendet:**
   - `locosoft_session()` → verbindet zu `loco_auswertung_db` (externe Locosoft-DB)
   - `FROM times` (77 Stellen in `werkstatt_data.py`)
   - `FROM orders` ✅ (existiert)
   - `FROM labours` ✅ (existiert)

2. **In Locosoft-DB (`loco_auswertung_db`):**
   - ✅ `orders` (BASE TABLE) - existiert
   - ✅ `labours` (BASE TABLE) - existiert
   - ❌ `times` (VIEW) - **existiert NICHT**
   - ❌ `loco_times` - existiert NICHT (wird nur in Portal-DB gespiegelt)

3. **In Portal-DB (`drive_portal`):**
   - ✅ `loco_times` (BASE TABLE) - 194.004 Zeilen (gespiegelt)

4. **Sync-Script (`locosoft_mirror.py`):**
   - Versucht `times` als VIEW zu spiegeln (Zeile 84: `INCLUDE_VIEWS = ['times', 'employees']`)
   - Aber `times` existiert nicht in Locosoft-DB → kann nicht gespiegelt werden

### Git-Historie

- Code verwendet schon immer `FROM times` mit `locosoft_session()`
- Keine Migration von `loco_times` zu `times`
- Dokumentation erwähnt `times (VIEW)`, aber View wurde nie erstellt

### Betroffene Dateien

1. **`api/werkstatt_data.py`** (77 Stellen mit `FROM times`)
   - `get_stempelungen_dedupliziert()`
   - `get_stempelzeit_locosoft()`
   - `get_stempelzeit_leistungsgrad()`
   - `get_stempelungen_roh()`
   - `get_anwesenheit_rohdaten()`
   - `get_st_anteil_position_basiert()`
   - `get_stempeluhr()`
   - `get_heute_live()`

2. **`celery_app/tasks.py`** (2 Stellen mit `FROM times`)
   - `benachrichtige_serviceberater_ueberschreitungen()`

## 💡 Lösungsoptionen

### Option 1: VIEW in Locosoft-DB erstellen (EMPFOHLEN)

**Voraussetzung:** Berechtigung zum Erstellen von Views in Locosoft-DB

```sql
-- In Locosoft-DB (loco_auswertung_db) ausführen:
CREATE VIEW times AS SELECT * FROM <echte_tabelle>;
```

**Problem:** Wir wissen nicht, welche Tabelle `times` ersetzen soll!

**Mögliche Quellen:**
- Vielleicht existiert `times` in einem anderen Schema (`private`, `app2`)?
- Oder wurde `times` gelöscht/umbenannt?

### Option 2: Code ändern - Portal-DB verwenden

**Änderung:** `werkstatt_data.py` verwendet `db_session()` statt `locosoft_session()` für `times`

**Vorteile:**
- `loco_times` existiert bereits in Portal-DB (194.004 Zeilen)
- Keine Berechtigungsprobleme
- Daten sind bereits gespiegelt

**Nachteile:**
- Daten könnten veraltet sein (Sync läuft täglich um 19:00)
- Mischung aus zwei Datenbanken (Locosoft für `orders`/`labours`, Portal für `times`)

**Code-Änderung:**
```python
# Statt:
with locosoft_session() as conn:
    cursor.execute("SELECT * FROM times ...")

# Verwende:
from api.db_connection import get_db
conn = get_db()
cursor.execute("SELECT * FROM loco_times ...")
```

### Option 3: Tabellennamen im Code ändern

**Änderung:** Alle `FROM times` → `FROM <echte_tabelle>`

**Problem:** Wir wissen nicht, wie die echte Tabelle heißt!

## 🎯 Empfohlene Lösung

**Option 2: Code ändern - Portal-DB verwenden**

**Begründung:**
1. `loco_times` existiert bereits in Portal-DB
2. Daten werden täglich um 19:00 gespiegelt (ausreichend aktuell)
3. Keine Berechtigungsprobleme
4. Einfachste Lösung

**Umsetzung:**
1. Neue Funktion `get_times_connection()` in `werkstatt_data.py`
2. Verwendet `get_db()` für `loco_times` aus Portal-DB
3. Alle `FROM times` → `FROM loco_times`
4. Alle `locosoft_session()` → `db_session()` für `times`-Queries

## 📋 Nächste Schritte

1. ✅ **Analyse abgeschlossen** - Problem identifiziert
2. ⏳ **Lösung implementieren** - Option 2 (Portal-DB verwenden)
3. ⏳ **Tests durchführen** - Alle betroffenen Endpoints prüfen
4. ⏳ **Service neustarten** - Nach Fix

## Betroffene Endpoints

- `/werkstatt/stempeluhr` → `get_stempeluhr()` → verwendet `times`
- `/werkstatt/cockpit` → verwendet `get_stempeluhr()` → verwendet `times`
- `/werkstatt/stempeluhr/monitor` → verwendet `get_stempeluhr()` → verwendet `times`
- `/werkstatt/leistung` → `get_mechaniker_leistung()` → verwendet `times`
- Celery Task: `benachrichtige_serviceberater_ueberschreitungen()` → verwendet `times`
