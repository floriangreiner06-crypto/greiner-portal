# TAG 136 - PostgreSQL Migration Status

**Datum:** 2025-12-23
**Status:** In Bearbeitung

---

## Erledigt (TAG 135 + 136)

### Sync-Scripts (Schreiben in unsere DB)
| Script | Status | Bemerkung |
|--------|--------|-----------|
| `scripts/sync/locosoft_mirror.py` | OK | PostgreSQL → PostgreSQL |
| `scripts/sync/bwa_berechnung.py` | OK | SUBSTRING() statt substr() |
| `scripts/sync/sync_employees.py` | OK | %s Placeholders |
| `scripts/sync/sync_sales.py` | OK | ON CONFLICT |
| `scripts/sync/sync_werkstatt_zeiten.py` | OK | DISTINCT ON, INTERVAL |
| `celery_app/tasks.py` | OK | pg_dump für Backup |

### Abstraktions-Layer
| Datei | Status | Funktion |
|-------|--------|----------|
| `api/db_connection.py` | OK | Dual-Mode SQLite/PostgreSQL |
| `api/db_utils.py` | OK | Nutzt jetzt db_connection.py |

---

## Migriert (TAG 136)

### API-Dateien

| Datei | Status | Bemerkung |
|-------|--------|-----------|
| `api/admin_api.py` | ✅ ERLEDIGT | STRING_AGG vs GROUP_CONCAT |
| `api/parts_api.py` | ✅ ERLEDIGT | db_session, sql_placeholder |
| `api/jahrespraemie_api.py` | ✅ ERLEDIGT | PraemienRechner Klasse |
| `api/leasys_api.py` | ✅ ERLEDIGT | Cache mit EXTRACT(EPOCH) |
| `api/ml_api.py` | ✅ ERLEDIGT | Mechaniker-Namen laden |
| `api/werkstatt_live_api.py` | ✅ ERLEDIGT | ServiceBox-Abfrage |

### Import-Scripts (aktive)

| Script | Status | Bemerkung |
|--------|--------|-----------|
| `scripts/imports/import_mt940.py` | ✅ ERLEDIGT | MT940 Bankdaten |
| `scripts/imports/import_santander.py` | ✅ ERLEDIGT | Fahrzeugfinanzierungen |
| `scripts/imports/import_servicebox.py` | ✅ ERLEDIGT | ServiceBox JSON Import |

### Import-Scripts (Legacy/selten genutzt - noch zu prüfen)

| Script | Problem |
|--------|---------|
| `scripts/imports/import_hyundai.py` | sqlite3, selten genutzt |
| `scripts/imports/import_stellantis.py` | sqlite3, selten genutzt |
| `scripts/imports/import_teile.py` | sqlite3, selten genutzt |

### E-Mail Reports (mit Feiertagskalender)

| Script | Status | Bemerkung |
|--------|--------|-----------|
| `scripts/send_daily_tek.py` | ✅ ERLEDIGT | db_session + is_holiday() |
| `scripts/send_daily_auftragseingang.py` | ✅ ERLEDIGT | db_session + is_holiday() |

**Feiertagskalender-Feature:**
- Nutzt `year_calendar.is_public_holid` aus Locosoft PostgreSQL
- Prüft beim Start ob heute ein Feiertag ist
- Zusätzlicher Wochenend-Check als Sicherheit
- Bei Feiertag: Exit mit 0, kein E-Mail-Versand

---

## SQL-Inkompatibilitäten Checkliste

| SQLite | PostgreSQL | Wo anpassen |
|--------|------------|-------------|
| `?` | `%s` | convert_placeholders() nutzen |
| `GROUP_CONCAT(x, ', ')` | `STRING_AGG(x, ', ')` | admin_api.py |
| `substr()` | `SUBSTRING()` | Bereits gefixt |
| `datetime('now')` | `NOW()` | sql_now() nutzen |
| `strftime('%Y', col)` | `EXTRACT(YEAR FROM col)` | sql_year() nutzen |
| `IFNULL()` | `COALESCE()` | sql_ifnull() nutzen |
| `INSERT OR REPLACE` | `ON CONFLICT DO UPDATE` | Manuell |

---

## Helper-Funktionen in db_connection.py

```python
# Placeholder: ? oder %s
sql_placeholder()

# Konvertiert ? zu %s für PostgreSQL
convert_placeholders(sql)

# Datum/Zeit
sql_now()       # NOW() vs datetime('now')
sql_date(col)   # ::DATE vs DATE()
sql_year(col)   # EXTRACT vs strftime
sql_month(col)  # EXTRACT vs strftime
```

---

## Empfohlene Vorgehensweise

1. **Kurzfristig (Muss funktionieren):**
   - admin_api.py fixen (Rechteverwaltung wird aktiv genutzt)
   - GROUP_CONCAT-Problem lösen

2. **Mittelfristig:**
   - Alle API-Dateien auf db_session() umstellen
   - Import-Scripts prüfen und anpassen

3. **Langfristig:**
   - SQLite vollständig entfernen
   - Alle Tests auf PostgreSQL laufen lassen

---

## Rollback-Option

Falls Probleme: In `/opt/greiner-portal/config/.env`:
```
DB_TYPE=sqlite
```
Dann: `sudo systemctl restart greiner-portal`
