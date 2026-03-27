# TODO FOR CLAUDE - SESSION START TAG 137

**Erstellt:** 2025-12-23
**Vorherige Session:** TAG 136 - PostgreSQL Migration Bugfixes

---

## Kontext

TAG 136 hat die PostgreSQL-Migration für Controlling, Bankenspiegel und Werkstatt APIs repariert. Die wichtigsten Patterns für die Migration sind:

1. **Placeholders:** `?` → `%s` via `convert_placeholders()` oder `{ph}` mit `sql_placeholder()`
2. **Boolean:** `aktiv = 1` → `aktiv = true` (dynamisch mit `get_db_type()`)
3. **Datumsfunktionen:** `date('now', '-X days')` → `CURRENT_DATE - INTERVAL 'X days'`
4. **Decimal:** PostgreSQL gibt `Decimal` zurück - `float()` für Arithmetik
5. **Row-Zugriff:** `row_to_dict()` und `rows_to_list()` verwenden

---

## Offene PostgreSQL-Migration Aufgaben

### Zu prüfende APIs (potentiell betroffen)

Diese APIs nutzen möglicherweise noch SQLite-spezifische Syntax:

1. **Urlaubsplaner APIs**
   - `api/vacation_api.py`
   - `api/vacation_chef_api.py`
   - `api/vacation_admin_api.py`

2. **Verkauf APIs**
   - `api/verkauf_api.py`
   - `api/leasys_api.py` (bereits teilweise migriert)

3. **Teile/Aftersales APIs**
   - `api/teile_api.py`
   - `api/teile_status_api.py`

4. **Weitere Controlling**
   - `api/auftrag_api.py`
   - `api/dashboard_api.py`

### Suchpattern für problematischen Code

```bash
# SQLite Placeholders finden
grep -r "cursor.execute.*\?" api/ --include="*.py"

# SQLite date() Funktion
grep -r "date('now'" api/ --include="*.py"

# Boolean als Integer
grep -rE "aktiv\s*=\s*[01]" api/ --include="*.py"
grep -rE "is_latest_record\s*=\s*[01]" api/ --include="*.py"
```

---

## Allgemeine Aufgaben (nicht PostgreSQL-spezifisch)

1. **Comprehensive Testing** - Alle Module einmal durchklicken nach Migration
2. **Dokumentation** - `docs/TAG136_DB_MIGRATION_STATUS.md` vervollständigen
3. **Performance-Check** - PostgreSQL Queries auf langsame Abfragen prüfen

---

## Wichtige Imports für PostgreSQL-Kompatibilität

```python
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import (
    get_db_type,
    convert_placeholders,
    sql_placeholder
)
```

---

## Befehle für Server

```bash
# Dateien syncen
rsync -av /mnt/greiner-portal-sync/api/ /opt/greiner-portal/api/

# Service neustarten
sudo systemctl restart greiner-portal

# Logs prüfen
journalctl -u greiner-portal -f

# Fehler suchen
journalctl -u greiner-portal --since "5 minutes ago" | grep -i error
```

---

## Git Status (Stand TAG 136 Ende)

26+ geänderte Dateien - hauptsächlich API-Anpassungen für PostgreSQL.

Wichtigste Änderungen:
- `api/zins_optimierung_api.py`
- `api/bankenspiegel_api.py`
- `api/werkstatt_api.py`
- `routes/controlling_routes.py`

---

## Hinweise

- **Templates brauchen keinen Restart** - nur Browser-Refresh
- **Python-Änderungen brauchen Restart** - `sudo systemctl restart greiner-portal`
- **Sync-Pfad:** `/mnt/greiner-portal-sync/` (NICHT `/mnt/greiner-sync/`)
