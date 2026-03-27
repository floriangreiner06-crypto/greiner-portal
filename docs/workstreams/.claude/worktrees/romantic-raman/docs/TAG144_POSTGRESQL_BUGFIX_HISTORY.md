# PostgreSQL Migration - Bugfix History

**Erstellt:** 2025-12-29 (TAG 144)
**Status:** Laufende Bugfixes nach Migration

---

## Chronologie der Bugs und Fixes

### TAG 136 (2025-12-23) - Erste Migrations-Welle

| Bug | Ursache | Fix | Betroffene Dateien |
|-----|---------|-----|-------------------|
| `?` Placeholder funktioniert nicht | PostgreSQL nutzt `%s` | `convert_placeholders()` | Alle API-Dateien |
| `GROUP_CONCAT` fehlt | PostgreSQL nutzt `STRING_AGG` | Manuell ersetzt | admin_api.py |
| `datetime('now')` funktioniert nicht | PostgreSQL nutzt `NOW()` | `sql_now()` Helper | Diverse |
| `strftime` fehlt | PostgreSQL nutzt `EXTRACT` | `sql_year()`, `sql_month()` | Diverse |
| `IFNULL` fehlt | PostgreSQL nutzt `COALESCE` | `sql_ifnull()` Helper | Diverse |

**Gefixt in TAG 136:**
- admin_api.py - STRING_AGG
- parts_api.py - db_session, sql_placeholder
- jahrespraemie_api.py - PraemienRechner
- leasys_api.py - EXTRACT(EPOCH)
- ml_api.py - Mechaniker-Namen
- werkstatt_live_api.py - ServiceBox
- scripts/imports/import_mt940.py
- scripts/imports/import_santander.py
- scripts/imports/import_servicebox.py
- scripts/send_daily_tek.py
- scripts/send_daily_auftragseingang.py

---

### TAG 137-138 - TEK Drill-Down

| Bug | Ursache | Fix |
|-----|---------|-----|
| TEK Stückzahlen falsch | Doppelte Buchungen pro Fahrzeug | COUNT(DISTINCT VIN) statt Buchungen |
| DB1-Berechnung | Decimal/Float Inkompatibilität | float() Wrapper |

---

### TAG 139 - HybridRow

| Bug | Ursache | Fix |
|-----|---------|-----|
| `row['column']` vs `row[0]` | SQLite: Dict-like, PostgreSQL: Tuple | `HybridRow` Wrapper-Klasse |
| Gemischte Zugriffsmuster | Code nutzt beide Stile | `row_to_dict()`, `rows_to_list()` |

**HybridRow in api/db_connection.py:**
```python
class HybridRow:
    """Wrapper für DB-Rows mit dict-like UND index-Zugriff"""
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._dict[key]
```

---

### TAG 144 (2025-12-29) - Auto-Increment Fix

**KRITISCHER BUG:**
```
ERROR: null value in column "id" of relation "user_roles" violates not-null constraint
```

| Bug | Ursache | Fix |
|-----|---------|-----|
| INSERT ohne ID schlägt fehl | Fehlende SERIAL/Sequence auf id-Spalten | Sequences für alle 55 Tabellen erstellt |
| User-Login schlägt fehl | `user_roles` INSERT ohne Auto-ID | `user_roles_id_seq` erstellt |

**Betroffene Tabellen (55 Stück):**
- ad_group_role_mapping
- audit_log
- auth_audit_log
- banken
- carloop_fahrzeuge
- carloop_reservierungen
- charge_types_sync
- customers_suppliers
- dealer_vehicles
- departments
- ek_finanzierung_konditionen
- employees
- fahrzeugfinanzierungen
- fahrzeugfinanzierungen_new
- fibu_buchungen
- finanzierung_snapshots
- finanzierungsbanken
- holidays
- import_log
- konten
- konto_snapshots
- kreditlinien
- kreditlinien_snapshots
- ldap_employee_mapping
- leasys_vehicle_cache
- loco_financing_examples
- loco_leasing_examples
- manager_assignments
- praemien_berechnungen
- praemien_exporte
- praemien_kulanz_regeln
- praemien_mitarbeiter
- report_subscriptions
- roles
- salden
- sales
- santander_zins_staffel
- sessions
- stellantis_bestellungen
- stellantis_positionen
- sync_log
- sync_status
- system_job_history
- system_jobs
- teile_lieferscheine
- tilgungen
- transaktionen
- users
- user_roles (bereits separat gefixt)
- vacation_adjustments
- vacation_approval_rules
- vacation_audit_log
- vacation_bookings
- vacation_entitlements
- vacation_types
- vehicles

**Fix-SQL (wurde ausgeführt):**
```sql
-- Für jede Tabelle:
CREATE SEQUENCE IF NOT EXISTS {table}_id_seq;
SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false);
ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{table}_id_seq');
ALTER SEQUENCE {table}_id_seq OWNED BY {table}.id;
```

---

## Bekannte Pattern-Probleme

### 1. Boolean-Vergleiche
```python
# SQLite: aktiv = 1
# PostgreSQL: aktiv = true

# LÖSUNG: Dynamisch anpassen
if is_postgresql():
    sql = sql.replace('= 1', '= true').replace('= 0', '= false')
```

### 2. Datum-Arithmetik
```python
# SQLite: date('now', '-30 days')
# PostgreSQL: CURRENT_DATE - INTERVAL '30 days'

# LÖSUNG: sql_date_subtract() nutzen
```

### 3. Row-Zugriff
```python
# SQLite: row['column_name']
# PostgreSQL (ohne RealDictCursor): row[0]

# LÖSUNG: row_to_dict() oder HybridRow
```

### 4. Placeholder
```python
# SQLite: WHERE id = ?
# PostgreSQL: WHERE id = %s

# LÖSUNG: convert_placeholders(sql)
```

### 5. Auto-Increment
```python
# SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
# PostgreSQL: SERIAL PRIMARY KEY (oder manuell Sequence)

# LÖSUNG: Sequences erstellen (siehe TAG 144 Fix)
```

---

## Prüf-Query für fehlende Sequences

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'id'
  AND table_schema = 'public'
  AND column_default IS NULL
  AND is_nullable = 'NO'
ORDER BY table_name;
```

Wenn Ergebnis > 0 Zeilen: Sequences fehlen!

---

## Empfehlung für zukünftige Tabellen

Bei `CREATE TABLE` immer:
```sql
CREATE TABLE new_table (
    id SERIAL PRIMARY KEY,  -- SERIAL statt INTEGER
    ...
);
```

Oder explizit:
```sql
CREATE SEQUENCE new_table_id_seq;
CREATE TABLE new_table (
    id INTEGER PRIMARY KEY DEFAULT nextval('new_table_id_seq'),
    ...
);
```

---

## Rollback-Option

Falls kritische Probleme: In `/opt/greiner-portal/config/.env`:
```
DB_TYPE=sqlite
```
Dann: `sudo systemctl restart greiner-portal`

**WARNUNG:** Nach längerem PostgreSQL-Betrieb ist Rollback nicht mehr möglich ohne Datenverlust!
