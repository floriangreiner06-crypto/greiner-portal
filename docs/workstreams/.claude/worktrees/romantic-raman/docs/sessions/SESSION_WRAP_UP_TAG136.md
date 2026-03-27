# SESSION WRAP-UP TAG 136

**Datum:** 2025-12-23
**Fokus:** PostgreSQL Migration - Bugfixes für Controlling, Bankenspiegel & Werkstatt APIs

---

## Erledigte Aufgaben

### 1. Zinsen/Zinsanalyse APIs repariert
**Dateien:** `api/zins_optimierung_api.py`

**Problem:** `psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer` bei `k.aktiv = 1`

**Lösung:**
- Dynamischer `aktiv_check` basierend auf `get_db_type()`
- `aktiv = true` für PostgreSQL, `aktiv = 1` für SQLite
- Imports hinzugefügt: `row_to_dict`, `rows_to_list`, `get_db_type`, `convert_placeholders`

```python
aktiv_check = "k.aktiv = true" if get_db_type() == 'postgresql' else "k.aktiv = 1"
```

### 2. Einkaufsfinanzierung API repariert
**Dateien:** `api/bankenspiegel_api.py`

**Problem:** `?` Placeholders wurden nicht zu `%s` konvertiert

**Lösung:**
- Import von `sql_placeholder` hinzugefügt
- `{ph}` Pattern für parametrisierte Queries
- `row_to_dict()` für konsistenten Row-Zugriff

### 3. Transaktionen API repariert
**Dateien:** `api/bankenspiegel_api.py`

**Problem:** `syntax error at or near "ORDER" LINE 22: AND t.konto_id = ? ORDER BY`

**Lösung:**
- `convert_placeholders()` für alle drei Queries (Haupt-Query, Count, Stats)
- `rows_to_list()` für fetchall() Ergebnisse

### 4. Werkstatt Leistungsübersicht API repariert
**Dateien:** `api/werkstatt_api.py`

**Mehrere Probleme:**
1. `?` Placeholder nicht konvertiert
2. `date('now', '-X days')` SQLite-Funktion
3. `is_latest_record = 1` Boolean-Vergleich
4. `decimal.Decimal` Multiplikationsfehler

**Lösungen:**
```python
# Datum-Filter für PostgreSQL
if get_db_type() == 'postgresql':
    datum_filter = f"datum >= CURRENT_DATE - INTERVAL '{tage} days'"
else:
    datum_filter = "datum >= date('now', ?)"

# Boolean-Check
aktiv_check = "is_latest_record = true" if get_db_type() == 'postgresql' else "is_latest_record = 1"

# Decimal zu float konvertieren
gesamt_auftraege = sum(float(m['auftraege'] or 0) for m in mechaniker)
```

### 5. Werkstatt Produktivität in Controlling repariert
**Dateien:** `routes/controlling_routes.py`

**Problem:** Gleiche `?` Placeholder-Probleme

**Lösung:**
- `sql_placeholder()` und `convert_placeholders()` hinzugefügt
- `row_to_dict()` für konsistenten Zugriff

---

## PostgreSQL Migration Patterns (Referenz)

| SQLite | PostgreSQL | Pattern |
|--------|------------|---------|
| `?` | `%s` | `convert_placeholders(query)` oder `{ph}` mit `sql_placeholder()` |
| `aktiv = 1` | `aktiv = true` | `aktiv_check = "aktiv = true" if get_db_type() == 'postgresql' else "aktiv = 1"` |
| `date('now', '-X days')` | `CURRENT_DATE - INTERVAL 'X days'` | Dynamische Query-Konstruktion |
| `dict(row)` | `dict(row)` | Besser: `row_to_dict(row)` |
| `cursor.fetchall()` | `cursor.fetchall()` | Besser: `rows_to_list(cursor.fetchall())` |
| Integer/Float | `Decimal` | `float()` Wrapper für Arithmetik |

---

## Geänderte Dateien

### API-Dateien
- `api/zins_optimierung_api.py` - Zinsen Dashboard & Report
- `api/bankenspiegel_api.py` - Einkaufsfinanzierung & Transaktionen
- `api/werkstatt_api.py` - Werkstatt Leistungsübersicht
- `api/controlling_api.py` - TEK Dashboard (vorherige Session)
- `api/serviceberater_api.py` - Serviceberater APIs

### Route-Dateien
- `routes/controlling_routes.py` - Werkstatt Produktivität

### Weitere geänderte Dateien (aus vorherigen TAG 136 Sessions)
- `api/admin_api.py`
- `api/jahrespraemie_api.py`
- `api/leasys_api.py`
- `api/ml_api.py`
- `api/parts_api.py`
- `api/werkstatt_live_api.py`
- `celery_app/tasks.py`
- `scripts/imports/import_mt940.py`
- `scripts/imports/import_santander.py`
- `scripts/imports/import_servicebox.py`
- `scripts/send_daily_auftragseingang.py`
- `scripts/send_daily_tek.py`
- `scripts/sync/bwa_berechnung.py`
- `scripts/sync/locosoft_mirror.py`
- `scripts/sync/sync_employees.py`
- `scripts/sync/sync_sales.py`
- `scripts/sync/sync_werkstatt_zeiten.py`

---

## Getestete Endpunkte (funktionierend)

- `/api/zinsen/dashboard`
- `/api/zinsen/report`
- `/api/bankenspiegel/dashboard` (Gesamtsaldo, Transaktionen, Kategorien)
- `/api/bankenspiegel/konten` (12 Konten, View funktioniert)
- `/api/bankenspiegel/transaktionen` (16.614 Transaktionen)
- `/api/bankenspiegel/einkaufsfinanzierung`
- `/api/werkstatt/leistung` (12 Mechaniker, LG 75.1%)

---

### 6. Bankenspiegel Dashboard & Konten View repariert
**Dateien:** `api/bankenspiegel_api.py`, PostgreSQL View

**Problem:**
- View `v_aktuelle_kontostaende` existierte nicht in PostgreSQL
- Tabelle hieß `konto_snapshots` statt `kontostand_historie`
- SQLite-spezifische Funktionen im Dashboard

**Lösung:**
1. PostgreSQL View erstellt mit korrekten Spalten:
```sql
CREATE VIEW v_aktuelle_kontostaende AS
SELECT
    k.id, k.bank_id, b.bank_name, k.kontoname, k.iban, k.kontotyp,
    k.waehrung, COALESCE(k.kreditlinie, 0) as kreditlinie,
    k.anzeige_gruppe, k.sort_order,
    COALESCE(ks.kapitalsaldo, 0.0) as saldo,
    ks.stichtag as letztes_update, k.aktiv
FROM konten k
JOIN banken b ON k.bank_id = b.id
LEFT JOIN konto_snapshots ks ON k.id = ks.konto_id
    AND ks.stichtag = (SELECT MAX(stichtag) FROM konto_snapshots WHERE konto_id = k.id)
WHERE k.aktiv = true;
```

2. Dashboard-Queries PostgreSQL-kompatibel:
   - `DATE('now', '-30 days')` → `CURRENT_DATE - INTERVAL '30 days'`
   - `DATE('now', 'start of month')` → `DATE_TRUNC('month', CURRENT_DATE)`
   - `strftime('%Y-%m', datum)` → `TO_CHAR(datum, 'YYYY-MM')`
   - `aktiv = 1` → `aktiv = true`

---

## Bekannte Issues

1. **Weitere APIs könnten betroffen sein** - Es wurden nur die gemeldeten Fehler gefixt. Andere APIs mit ähnlichen Patterns könnten noch Probleme haben.

2. **Server muss nach Sync neugestartet werden:**
   ```bash
   sudo systemctl restart greiner-portal
   ```

---

## Server-Status

Die Änderungen wurden auf den Server gesynct und der Service neu gestartet.

---

## Nächste Schritte

Siehe `TODO_FOR_CLAUDE_SESSION_START_TAG137.md`
