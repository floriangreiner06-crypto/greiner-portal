# Urlaubsansprüche Fix - Ausführung auf Server

**TAG 167** - Alle Mitarbeiter zeigen "0" Tage Urlaubsanspruch

---

## Problem

View `v_vacation_balance_2025` verwendet SQLite-Syntax (`strftime`) statt PostgreSQL (`EXTRACT`).

---

## Lösung: 2 Schritte

### Schritt 1: View-Fix ausführen

```bash
# Auf Server (10.80.80.20)
ssh ag-admin@10.80.80.20

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
```

### Schritt 2: Diagnose prüfen

```bash
# Diagnose-Script ausführen
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/checks/check_vacation_entitlements.py
```

---

## Dateien (bereit)

✅ `scripts/migrations/fix_vacation_balance_view_postgresql.sql`  
✅ `scripts/checks/check_vacation_entitlements.py`  
✅ `scripts/checks/check_vacation_entitlements_simple.py` (einfache Version)

---

## Falls vacation_entitlements leer ist

```sql
-- Standard-Ansprüche für alle aktiven Mitarbeiter erstellen
INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually)
SELECT 
    id,
    2025,
    27.0,  -- Standard
    0.0,
    0.0
FROM employees
WHERE aktiv = true
  AND id NOT IN (SELECT employee_id FROM vacation_entitlements WHERE year = 2025)
ON CONFLICT (employee_id, year) DO NOTHING;
```

---

**Status:** ⏳ Scripts bereit, warten auf Server-Ausführung

