# Urlaubsansprüche Fix - TAG 167

**Datum:** 2026-01-05  
**Problem:** Alle Mitarbeiter zeigen "0" Tage Urlaubsanspruch  
**Status:** 🔧 Fix bereit für Server-Ausführung

---

## Problem

Nach der PostgreSQL-Migration zeigen alle Mitarbeiter "0" Tage Urlaubsanspruch.

**Ursache:** View `v_vacation_balance_2025` verwendet SQLite-Syntax (`strftime('%Y', ...)`) statt PostgreSQL (`EXTRACT(YEAR FROM ...)`).

---

## Lösung

### Schritt 1: View-Fix auf Server ausführen

```bash
# Auf Server einloggen
ssh ag-admin@10.80.80.20

# Zum Projekt-Verzeichnis
cd /opt/greiner-portal

# View-Fix ausführen
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f scripts/migrations/fix_vacation_balance_view_postgresql.sql
```

**Erwartete Ausgabe:**
```
DROP VIEW
CREATE VIEW
COMMENT
 anzahl_mitarbeiter 
--------------------
                 76
(1 row)

 employee_id |        name         | anspruch | verbraucht | geplant | resturlaub 
-------------+---------------------+----------+------------+---------+------------
 ...
```

### Schritt 2: Diagnose-Script ausführen

```bash
# Auf Server
cd /opt/greiner-portal
source venv/bin/activate  # Falls venv vorhanden
python3 scripts/checks/check_vacation_entitlements.py
```

**Das Script prüft:**
- ✅ Ob Tabelle `vacation_entitlements` existiert
- ✅ Anzahl Einträge in `vacation_entitlements`
- ✅ Einträge pro Jahr
- ✅ Mitarbeiter ohne Anspruch
- ✅ View-Funktionalität
- ✅ View-Definition (SQLite vs PostgreSQL Syntax)

### Schritt 3: Falls vacation_entitlements leer ist

Wenn das Diagnose-Script zeigt, dass `vacation_entitlements` leer ist:

```bash
# Standard-Ansprüche für alle aktiven Mitarbeiter erstellen
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal <<EOF
INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually)
SELECT 
    id,
    2025,
    27.0,  -- Standard-Urlaubsanspruch
    0.0,
    0.0
FROM employees
WHERE aktiv = true
  AND id NOT IN (SELECT employee_id FROM vacation_entitlements WHERE year = 2025)
ON CONFLICT (employee_id, year) DO NOTHING;
EOF
```

---

## Dateien

- ✅ `scripts/migrations/fix_vacation_balance_view_postgresql.sql` - View-Fix
- ✅ `scripts/checks/check_vacation_entitlements.py` - Diagnose-Script

---

## Nach dem Fix

1. **View testen:**
```sql
SELECT employee_id, name, anspruch, verbraucht, geplant, resturlaub 
FROM v_vacation_balance_2025 
WHERE anspruch > 0 
LIMIT 5;
```

2. **Im Portal prüfen:**
- Urlaubsplaner öffnen
- Eigener Urlaubsanspruch sollte angezeigt werden (nicht mehr "0")

---

## Troubleshooting

**Problem:** View existiert nicht
```sql
-- View manuell erstellen
\i scripts/migrations/fix_vacation_balance_view_postgresql.sql
```

**Problem:** View zeigt weiterhin 0
- Prüfe ob `vacation_entitlements` Daten hat: `SELECT COUNT(*) FROM vacation_entitlements WHERE year = 2025;`
- Prüfe ob `employees.aktiv = true` korrekt ist
- Prüfe View-Definition: `SELECT definition FROM pg_views WHERE viewname = 'v_vacation_balance_2025';`

---

**Status:** ⏳ Wartet auf Server-Ausführung

